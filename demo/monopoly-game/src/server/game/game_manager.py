# from datetime import datetime
# import random
#
# from .Bank import Bank
# from .player import Player
# from ..rooms.room_state import RoomState
# from ..network.packet_builder import PacketBuilder  # 🔗 Thêm import
#
# class GameManager:
#     """
#     Quản lý toàn bộ luồng chơi Monopoly:
#     - Điều phối lượt chơi
#     - Gọi hành động từ Player / Board / CardManager
#     - Cập nhật RoomState
#     - Phát sự kiện JSON tới client qua NetworkManager (chuẩn hóa bằng PacketBuilder)
#     """
#
#     def __init__(self, room_state: RoomState, board, card_manager, network, logger):
#         self.room_state = room_state
#         self.board = board
#         self.card_manager = card_manager
#         self.network = network
#         self.turn_manager = room_state.turn_manager
#         self.active = False
#         self.bank = Bank()
#         self.logger = logger
#
#         # Đăng ký Player vào Bank
#         for player in self.room_state.players:
#             player.bank = self.bank
#             self.bank.register_player(player, player.balance)
#
#     # -----------------------------------------------------
#     # 🕹️ Game Lifecycle
#     # -----------------------------------------------------
#     def start_game(self):
#         if self.active:
#             return
#         self.active = True
#         self.turn_manager.current_index = 0
#         self.room_state.status = "running"
#         self.room_state.start_time = datetime.now().isoformat()
#
#         packet = PacketBuilder.start_game(self.room_state.room_id, self.room_state.host_id)
#         packet["payload"]["players"] = [p.serialize() for p in self.room_state.players]
#         self.network.send_packet(packet)
#
#     def end_game(self, winner_id=None):
#         self.active = False
#         self.room_state.status = "ended"
#         self.room_state.end_time = datetime.now().isoformat()
#         self.room_state.winner = winner_id
#
#         packet = PacketBuilder.broadcast_state(
#             self.room_state.room_id,
#             {
#                 "action": "GAME_ENDED",
#                 "winner": winner_id,
#                 "timestamp": self.room_state.end_time,
#             },
#         )
#         self.network.send_packet(packet)
#
#     # -----------------------------------------------------
#     # 🔄 Turn Management
#     # -----------------------------------------------------
#     def get_current_player(self):
#         return self.turn_manager.get_current_player()
#
#     def next_turn(self):
#         """Chuyển lượt cho người chơi kế tiếp"""
#         self.get_current_player().has_rolled_and_moved = False
#         current = self.turn_manager.next_turn()
#
#         packet = PacketBuilder.broadcast_state(
#             self.room_state.room_id,
#             {
#                 "action": "TURN_CHANGED",
#                 "current_player": current.id,
#             },
#         )
#         self.network.send_packet(packet)
#
#     # -----------------------------------------------------
#     # 🎲 Player Actions
#     # -----------------------------------------------------
#     def roll_dice(self, player_id):
#         player = self.room_state.get_player(player_id)
#         if not player or not self.active:
#             return
#
#         # 🎲 Tung xúc xắc
#         dice_1, dice_2 = random.randint(1, 6), random.randint(1, 6)
#         total_steps = dice_1 + dice_2
#         is_double = (dice_1 == dice_2)
#         players = self.room_state.players
#
#         packet = PacketBuilder.roll_result(self.room_state.room_id, player.id, (dice_1, dice_2), total_steps, is_double)
#         self.network.send_packet(packet)
#
#         # 🎲 Xử lý ra đôi
#         if is_double:
#             player.consecutive_doubles += 1
#         else:
#             player.consecutive_doubles = 0
#
#         if player.consecutive_doubles == 3:
#             jail_tile = self.board.get_jail_tile()
#             player.position = jail_tile.tile_id
#             player.in_jail = True
#             player.consecutive_doubles = 0
#
#             jail_packet = PacketBuilder.send_to_jail(
#                 self.room_state.room_id, player.id, jail_tile.tile_id
#             )
#             self.network.send_packet(self.room_state.room_id, jail_packet)
#             self.next_turn()
#             return
#
#         # 📦 Di chuyển bình thường
#         move_result = self.board.move_player(player, total_steps, players)
#         tile_id = move_result["tile_id"]
#         tile = self.board.get_tile(tile_id)
#
#         # 💰 Qua ô GO
#         if move_result.get("passed_go"):
#             self.bank.pay_player(player, 200)
#             balance_packet = PacketBuilder.update_balance(
#                 self.room_state.room_id, player.id, player.balance
#             )
#             self.network.send_packet(self.room_state.room_id, balance_packet)
#
#         # 📡 Gửi gói tin thông báo di chuyển
#         move_packet = PacketBuilder.player_move(
#             self.room_state.room_id,
#             player.id,
#             tile_id,
#             (dice_1, dice_2),
#         )
#         self.network.send_packet(self.room_state.room_id, move_packet)
#
#         # ⚙️ Gọi logic từ Tile (tile tự quyết định event nào xảy ra)
#         tile_event = tile.on_land(player, self.board)
#
#
#         match tile_event.get("event"):
#             case "PAY_RENT":
#                 data = tile_event["data"]
#                 payer = player
#                 owner = self.room_state.get_player(data["owner_id"])
#                 amount = data["amount"]
#
#                 self.bank.transfer_between_players(payer, owner, amount)
#                 self.network.send_packet(PacketBuilder.update_balance(self.room_state.room_id, payer.id, payer.balance))
#                 self.network.send_packet(PacketBuilder.update_balance(self.room_state.room_id, owner.id, owner.balance))
#
#             case "BUY_PROPERTY":
#                 # Hiển thị prompt mua
#                 self.network.send_packet(PacketBuilder.prompt_buy_property(
#                     self.room_state.room_id,
#                     player.id,
#                     tile_event["data"]["tile_id"],
#                     tile_event["data"]["price"]
#                 ))
#
#             case "OWN_PROPERTY":
#                 # Gửi thông điệp đơn giản
#                 self.network.send_packet(PacketBuilder.info_message(
#                     self.room_state.room_id,
#                     tile_event["message"]
#                 ))
#
#         # 🔁 Chuyển lượt nếu không ra đôi
#         if not is_double:
#             player.consecutive_doubles = 0
#             self.next_turn()
#
#     def buy_property(self, player_id):
#         """Người chơi mua property hiện tại"""
#         player: 'Player' = self.room_state.get_player(player_id)
#         if not player or player.is_bankrupt:
#             return {"Notion": f"'{player.name} is bankrupted'"}
#
#         if not player.has_rolled_and_moved:
#             return {"Notion": f"'{player.name} must move before buying property'"}
#
#         tile = self.board.get_tile(player.position)
#         if tile.type != "property" or tile.owner_id is not None:
#             return {"Notion": f"'Property {tile.id} already owned by {tile.owner_id}'"}
#
#         result = player.bank.buy_property(player,tile)
#
#         if result["event"] == "buy_property" and result["status"] == "success":
#             self.bank.set_property_owner(tile.id, player.id)
#             tile.owner_id = player.id
#         elif result["event"] == "insufficient_funds":
#             return {"Notion": f"'{player.name} not have enough cash'"}
#         elif result["event"] == "player_has_not_moved":
#             return {"Notion": f"'{player.name} must move before buying property'"}
#
#         # Kiểm tra phá sản
#         if player.is_bankrupt:
#             self.handle_bankrupt(player)
#
#         packet = PacketBuilder.player_buy_property(
#             self.room_state.room_id,
#             str(player.id),
#             tile.tile_id,
#             tile.price,
#             result,
#         )
#         packet["payload"].update({
#             "balance": player.bank.get_balance(player),
#             "properties": player.properties,
#         })
#         self.network.send_packet(packet)
#         return None
#
#     # -----------------------------------------------------
#     # 💸 Bankrupt Handling
#     # -----------------------------------------------------
#     def handle_bankrupt(self, player):
#         self.logger.info(f"Player {player.name} (ID: {player.id}) went bankrupt.")
#
#         # Reset tài sản
#         self.bank.reset_property_owner(player.id)
#         for property_id in player.properties:
#             tile = self.board.get_tile(property_id)
#             if tile:
#                 tile.owner_id = None
#         player.properties = []
#         player.is_bankrupt = True
#
#         packet = PacketBuilder.error(
#             self.room_state.room_id,
#             player.id,
#             f"{player.name} has gone bankrupt."
#         )
#         self.network.send_packet(packet)
#         self.check_end_conditions()
#
#     # -----------------------------------------------------
#     # 🏁 End Conditions
#     # -----------------------------------------------------
#     def check_end_conditions(self):
#         active_players = [p for p in self.room_state.players if not p.is_bankrupt]
#         if len(active_players) <= 1:
#             winner = active_players[0].id if active_players else None
#             self.end_game(winner)
#
#     # -----------------------------------------------------
#     # 🔄 Sync / Utility
#     # -----------------------------------------------------
#     def force_sync(self):
#         """Gửi toàn bộ trạng thái phòng và board tới client"""
#         self.room_state.update_from_game(self.board, self.room_state.players)
#         state_data = {
#             "room": self.room_state.serialize(),
#             "board": self.board.get_board_state(),
#         }
#         packet = PacketBuilder.broadcast_state(self.room_state.room_id, state_data)
#         self.network.send_packet(packet)



# file: game/logic/game_manager.py
import random
from datetime import datetime
from ..network.packet_builder import PacketBuilder


class GameManager:
    """
    Quản lý toàn bộ luồng chơi Monopoly:
    - Điều phối lượt chơi
    - Gọi hành động từ Player / Board / Carnager
    - Cập nhật RoomState
    - Phát sự kiện JSON tới client qua NetworkManager (chuẩn hóa bằng PacketBuilder)
    """

    def __init__(self, room_state, board, network, logger):
        self.room_state = room_state    # Thông tin phòng hiện tại
        self.board = board              # Lớp xử lý toàn bộ logic game
        self.network = network          # NetworkManager
        self.logger = logger
        self.active = False
        self.turn_index = 0
        self.turn_order = []            # Danh sách ID người chơi theo thứ tự lượt

    # ----------------------------------------------------------------------
    # 🎮 GAME FLOW
    # ----------------------------------------------------------------------
    def start_game(self):
        """Khởi động game và chọn người đi đầu tiên."""
        self.active = True
        self.turn_order = list(self.room_state.players.keys())
        self.turn_index = 0
        first_player = self.room_state.get_player(self.turn_order[0])

        packet = PacketBuilder.game_start(self.room_state.room_id, first_player.id)
        self.network.send_packet(self.room_state.room_id, packet)
        self.logger.info(f"[GAME] Bắt đầu game tại phòng {self.room_state.room_id}")

    def next_turn(self):
        """Chuyển lượt sang người chơi kế tiếp."""
        self.turn_index = (self.turn_index + 1) % len(self.turn_order)
        next_player_id = self.turn_order[self.turn_index]
        next_player = self.room_state.get_player(next_player_id)

        packet = PacketBuilder.next_turn(self.room_state.room_id, next_player.id)
        self.network.send_packet(self.room_state.room_id, packet)
        self.logger.debug(f"[TURN] → {next_player.name}'s turn")

    # ----------------------------------------------------------------------
    # 🎲 COMMAND DISPATCHER
    # ----------------------------------------------------------------------
    def handle_command(self, command: str, player_id: str, data: dict = None):
        """
        Nhận lệnh từ client và ủy quyền xử lý cho Board.
        :param command: Tên lệnh ("ROLL_DICE", "BUY_PROPERTY", ...)
        :param player_id: Người gửi lệnh
        :param data: Dữ liệu kèm theo (nếu có)
        """
        player = self.room_state.get_player(player_id)
        if not player or not self.active:
            self.logger.warning(f"[GAME] Bỏ qua lệnh {command} (game chưa hoạt động hoặc player không tồn tại)")
            return

        # Bảng ánh xạ command → phương thức xử lý trong Board
        command_map = {
            "ROLL_DICE": self._cmd_roll_dice,
            "BUY_PROPERTY": self._cmd_buy_property,
            "END_TURN": self._cmd_end_turn,
        }

        handler = command_map.get(command)
        if handler:
            result_packets = handler(player, data)
            self._broadcast_packets(result_packets)
        else:
            self.logger.warning(f"[GAME] Lệnh không hợp lệ: {command}")

    # ----------------------------------------------------------------------
    # 🎯 COMMAND HANDLERS
    # ----------------------------------------------------------------------
    def _cmd_roll_dice(self, player, data=None):
        """Gọi board để xử lý việc tung xúc xắc."""
        dice_1, dice_2 = random.randint(1, 6), random.randint(1, 6)
        total_steps = dice_1 + dice_2

        # Ủy quyền xử lý di chuyển và logic trong Board
        results = self.board.handle_player_move(player, total_steps, (dice_1, dice_2))
        return results  # Board trả về list các packet chuẩn

    def _cmd_buy_property(self, player, data):
        """Người chơi quyết định mua property."""
        tile_id = data.get("tile_id")
        results = self.board.handle_buy_property(player, tile_id)
        return results

    def _cmd_end_turn(self, player, data=None):
        """Người chơi kết thúc lượt."""
        self.next_turn()
        return [PacketBuilder.info_message("END_TURN", f"{player.name} đã kết thúc lượt.")]

    # ----------------------------------------------------------------------
    # 🛰️ NETWORK HELPER
    # ----------------------------------------------------------------------
    def _broadcast_packets(self, packets):
        """Gửi danh sách packet tới tất cả client trong phòng."""
        if not packets:
            return
        if isinstance(packets, dict):
            packets = [packets]

        for pkt in packets:
            pkt["room_id"] = self.room_state.room_id
            self.network.send_packet(self.room_state.room_id, pkt, target="all")
