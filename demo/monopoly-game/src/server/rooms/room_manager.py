from datetime import datetime
from ..network.network_manager import NetworkManager
from ..game.game_manager import GameManager
from ..rooms.room_state import RoomState
from ..utils.logger import Logger
from ..game.player import Player
from ..game.board import Board
from ..game.card_manager2 import CardManager

class RoomManager:
    """
    Bộ điều phối cấp cao:
      - Kết nối GameManager ↔ RoomState ↔ NetworkManager
      - Tạo / xóa / quản lý phòng
      - Trung gian xử lý hành động từ client (roll, buy, end_turn, ...)
    """

    def __init__(self, networkmanager: 'NetworkManager',logger: Logger):
        self.logger = logger
        self.network = networkmanager
        self.rooms: dict[str, dict] = {}

        # Đăng ký callback cho các packet đến từ client
        self.network.register_listener("on_packet", self.handle_network_packet)

    # ----------------------------------------------------------------------
    # 📡 1️⃣ NHẬN DỮ LIỆU TỪ CLIENT
    # ----------------------------------------------------------------------
    async def handle_network_packet(self, packet: dict):
        """
        Callback cho NetworkManager mỗi khi có packet mới đến.
        """
        room_id = packet.get("room_id")
        data = packet.get("data", {})
        player_id = data.get("player_id")
        action = data.get("action")
        if not room_id or not action:
            self.logger.warning("Invalid packet received.")
            return
        if not isinstance(room_id, str):
            self.logger.warning(f"Invalid packet received: room_id is not a string. Skipping.")
            return
        if player_id is None:  # player_id có thể là 0, nên kiểm tra None thay vì not
            self.logger.warning(f"Invalid packet received: Missing player_id. Skipping.")
            return
        data = await self.handle_action(room_id, player_id, action)
        print(f"data của handle_network_packet ham handle_action  {data} :" )

    # ----------------------------------------------------------------------
    # 🏠 2️⃣ QUẢN LÝ PHÒNG
    # ----------------------------------------------------------------------
    async def create_room(self, room_id: str, host_id: str):
        """Tạo phòng mới và đăng ký group multicast."""
        if room_id in self.rooms:
            self.logger.warning(f"[ROOM] '{room_id}' already exists.")
            return None

        # Tạo group multicast riêng cho phòng này
        group = self.network.multicast.create_group(room_id)

        # Khởi tạo RoomState + GameManager
        room_board = Board()
        host_player = Player(player_id=host_id, name="Host Player",room_id=room_id,bank_service=room_board.bank)  # Giả định Player nhận id và name
        room_players = [host_player]
        card_manager = CardManager()
        state = RoomState(room_id=room_id, host_id=host_id, network=self.network, logger=self.logger,players =room_players,board = room_board )
        game_mgr = GameManager(state,room_board,card_manager,self.network, self.logger)

        # Đăng ký vào danh sách phòng
        self.rooms[room_id] = {
            "room_id": room_id,
            "host_id": host_id,
            "state": state,
            "game_mgr": game_mgr,
            "multicast_ip": group["ip"],
            "port": group["port"],
        }

        self.logger.success(f"[ROOM CREATED] {room_id} ({group['ip']}:{group['port']})")
        return {"room_id": room_id, "ip": group["ip"], "port": group["port"]}

    async def remove_room(self, room_id: str):
        """Xóa phòng và hủy group multicast."""
        if room_id not in self.rooms:
            return False

        self.network.multicast.remove_group(room_id)
        del self.rooms[room_id]
        self.logger.info(f"[ROOM REMOVED] {room_id}")
        return True

    async def list_rooms(self):
        """Trả danh sách phòng cho client."""
        return {
            rid: {
                "ip": info["multicast_ip"],
                "port": info["port"],
                "players": list(info["state"].players.keys()),
                "status": info["state"].status,
            }
            for rid, info in self.rooms.items()
        }

    # ----------------------------------------------------------------------
    # 👥 3️⃣ NGƯỜI CHƠI
    # ----------------------------------------------------------------------
    async def add_player(self, room_id: str, player_id: str, name: str):
        room = self.rooms.get(room_id)
        if not room:
            return {"error": "Room not found"}

        state = room["state"]
        state.add_player(player_id, name)

        if len(state.players) == state.max_players and state.status == RoomState.LOBBY:
            room["game_mgr"].start_game()
            state.status = RoomState.INGAME
            self.logger.info(f"[GAME START] Room {room_id} has begun!")
# start game ở chỗ này
        await self.sync_room_state(room_id)
        return state.serialize()


# nếu remove thì game asset tính sau ?
    async def remove_player(self, room_id: str, player_id: str):
        room = self.rooms.get(room_id)
        if not room:
            return {"error": "Room not found"}

        state = room["state"]
        state.remove_player(player_id)
        await self.sync_room_state(room_id)
        return {"ok": True}

    # ----------------------------------------------------------------------
    # 🎲 4️⃣ HÀNH ĐỘNG GAMEPLAY
    # ----------------------------------------------------------------------
    async def handle_action(self, room_id: str, player_id: str, action: str):
        """Chuyển hành động từ client sang GameManager."""
        room = self.rooms.get(room_id)
        state = room["state"]
        if state.turn_manager.get_current_player().id !=player_id:
            return 0


        if not room:
            return {"error": "Room not found"}

        game_mgr: GameManager = room["game_mgr"]
        state: RoomState = room["state"]
        # Player chỉ có thể start game khi game state = lobby
        if action =="start_game" :
            if state.status == RoomState.INGAME:
                result = {"error": f"Game has already started ''"}
                return result
            elif state.status == RoomState.FINISHED:
                result = {"error": f"Game has already ended ''"}
                return result
            else :
                if room["host_id"] == player_id:
                    result = game_mgr.start_game()
                    return result

                    # RoomState nên chuyển trạng thái (state.status = 'INGAME') ở đây hoặc trong GameManager
                else:
                    # Tuongw lai neen promt ddeer báo rằng mình sẫn sàng
                    result = {"error": "Only host can start the game"}
                    return result

        # Mapping hành động → Gọi hàm trong GameManager


        match action:
            case "roll_dice":
                result = game_mgr.roll_dice(player_id)
            case "buy_property":
                result = game_mgr.buy_property(player_id)
            case "end_turn":
                result = game_mgr.next_turn()
            # thêm case dùm card ra tù
            # thêm case check status player
            case _:
                result = {"error": f"Unknown action '{action}'"}

        # Đồng bộ lại toàn bộ trạng thái sau khi hành động
        state.update_from_game(game_mgr.board,game_mgr.room_state.players)
        await self.sync_room_state(room_id)
        return result

    # ----------------------------------------------------------------------
    # 🔄 5️⃣ ĐỒNG BỘ DỮ LIỆU
    # ----------------------------------------------------------------------
    async def sync_room_state(self, room_id: str):
        """Gửi toàn bộ snapshot của RoomState qua NetworkManager."""
        room = self.rooms.get(room_id)
        if not room:
            return
        packet = {
            "type": "ROOM_STATE_UPDATE",
            "room_id": room_id,
            "timestamp": datetime.now().isoformat(),
            "data": room["state"].serialize(),
        }

        # Gửi qua tầng mạng (multicast)
        self.network.send_packet(room_id, packet)
        self.logger.debug(f"[SYNC] Room {room_id} → broadcasted to group.")
