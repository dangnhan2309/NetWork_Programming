"""
Room Manager - Quản lý phòng chơi - PHIÊN BẢN ĐÃ SỬA (Fixed)
- Sửa các vấn đề về thời gian (dùng time.time())
- Sửa broadcast để không thay đổi dict khi lặp
- Thêm timeout khi gửi qua websocket
- Reset current_turn khi khởi tạo game
- Đồng bộ hóa trạng thái board['current_player'] khi chuyển lượt
- Sửa cleanup sử dụng time.time()
- Một vài cải tiến lỗi/exception handling
"""

import uuid
import asyncio
import json
import random
import time
from typing import Dict, List, Optional
from ..shared import constants as C


class Room:
    def __init__(self, room_id: str, room_name: str, max_players: int = 4):
        self.room_id = room_id
        self.room_name = room_name
        self.max_players = max_players
        self.required_players = 2
        # players: Dict[player_id, {name, websocket, is_host}]
        self.players: Dict[str, dict] = {}
        self.host_id: Optional[str] = None
        self.state = C.STATE_EMPTY
        self.marked_for_deletion = False
        self.empty_since: Optional[float] = None

        # Game state
        self.game_started = False
        self.current_turn = 0
        self.board: Optional[dict] = None
        self.dice_result = None

        # Optional: per-room lock if you later make add/remove async
        # self._lock = asyncio.Lock()

        print(f"🏠 Room initialized: {room_name} (ID: {room_id}), Max: {max_players}")

    def add_player(self, player_id: str, player_name: str, websocket, is_host: bool = False) -> bool:
        """Thêm player vào phòng (synchronous API giữ nguyên)
        Lưu ý: phương thức này không await; đảm bảo gọi trong luồng/coroutine phù hợp.
        """
        if len(self.players) >= self.max_players:
            print(f"❌ Room {self.room_id} is full ({len(self.players)}/{self.max_players})")
            return False

        if self.state not in [C.STATE_EMPTY, C.STATE_WAITING]:
            print(f"❌ Room {self.room_id} is not accepting players (state: {self.state})")
            return False

        self.players[player_id] = {
            'name': player_name,
            'websocket': websocket,
            'is_host': is_host
        }

        if is_host or not self.host_id:
            self.host_id = player_id
            self.players[player_id]['is_host'] = True

        # Cập nhật state
        if len(self.players) >= 1:
            self.state = C.STATE_WAITING

        # Nếu phòng trước đó được đánh dấu xóa nhưng có người join lại thì bỏ dấu
        if self.marked_for_deletion:
            self.marked_for_deletion = False
            self.empty_since = None

        print(f"✅ {player_name} joined room {self.room_name}. Now {len(self.players)}/{self.max_players} players")
        return True

    def remove_player(self, player_id: str) -> bool:
        """Xóa player khỏi phòng - KHÔNG tự động xóa phòng ngay lập tức (chỉ đánh dấu)
        Giữ API synchronous để tương thích.
        """
        if player_id in self.players:
            player_name = self.players[player_id]['name']
            print(f"🔧 DEBUG: Đang xóa player {player_name} (ID: {player_id})")

            # Xóa player
            del self.players[player_id]

            print(f"🔧 DEBUG: Còn lại {len(self.players)} players")

            # Nếu host rời đi, chọn host mới
            if player_id == self.host_id and self.players:
                new_host_id = next(iter(self.players.keys()))
                self.players[new_host_id]['is_host'] = True
                self.host_id = new_host_id
                print(f"🔧 DEBUG: Chuyển host cho {self.players[new_host_id]['name']}")

            # Cập nhật state
            if len(self.players) == 0:
                self.state = C.STATE_EMPTY
                self.empty_since = time.time()
                print(f"🔧 DEBUG: Room {self.room_id} is now empty")

                # CHỈ đánh dấu để xóa sau, không xóa ngay
                self.marked_for_deletion = True
            else:
                # Nếu đang chơi, giữ state PLAYING
                if self.game_started and self.state == C.STATE_PLAYING:
                    # không đổi sang WAITING nếu game vẫn diễn ra
                    print(f"🔧 DEBUG: Player left during play; still playing with {len(self.players)} players")
                else:
                    self.state = C.STATE_WAITING
                    print(f"🔧 DEBUG: Room {self.room_id} has {len(self.players)} players, state: {self.state}")

            return True
        return False

    def can_start_game(self) -> bool:
        """Kiểm tra có thể bắt đầu game không"""
        return len(self.players) >= self.required_players and self.state == C.STATE_WAITING

    async def start_game(self):
        """Bắt đầu game"""
        if not self.can_start_game():
            print(f"❌ Cannot start game: {len(self.players)}/{self.required_players} players or wrong state")
            return False

        self.state = C.STATE_PLAYING
        self.game_started = True

        # Khởi tạo game state (reset lượt)
        self._initialize_game()

        # Broadcast game started
        try:
            await self.broadcast({
                "type": C.TYPE_INFO,
                "event": C.EVENT_GAME_STARTED,
                "message": "🚀 Game started!",
                "board": self.get_board_state(),
                "currentTurn": self.get_current_player_id()
            })
        except Exception as e:
            print(f"⚠️ Warning: broadcast during start_game failed: {e}")

        print(f"🎮 Game started in room {self.room_id} with {len(self.players)} players")
        return True

    def _initialize_game(self):
        """Khởi tạo game state"""
        self.current_turn = 0
        self.board = {
            "players": [
                {
                    "id": pid,
                    "name": data['name'],
                    "position": 0,
                    "money": 1500,
                    "properties": []
                }
                for pid, data in self.players.items()
            ],
            "current_player": 0,
            "dice_result": None
        }

    def get_current_player_id(self) -> Optional[str]:
        """Lấy ID của người chơi hiện tại"""
        if not self.players:
            return None
        player_ids = list(self.players.keys())
        # bảo đảm current_turn không vượt quá số phần tử
        if len(player_ids) == 0:
            return None
        return player_ids[self.current_turn % len(player_ids)]

    def get_current_player(self) -> Optional[dict]:
        """Lấy thông tin người chơi hiện tại"""
        current_id = self.get_current_player_id()
        if current_id and current_id in self.players:
            return {
                "id": current_id,
                "name": self.players[current_id]['name'],
                "is_host": self.players[current_id]['is_host']
            }
        return None

    def next_turn(self):
        """Chuyển lượt"""
        if self.players:
            self.current_turn = (self.current_turn + 1) % len(self.players)
            # Đồng bộ lên board nếu có
            if self.board is not None:
                self.board["current_player"] = self.current_turn

    async def handle_roll_dice(self, player_id: str) -> dict:
        """Xử lý roll dice"""
        if player_id != self.get_current_player_id():
            return {
                "type": C.TYPE_ERROR,
                "message": "❌ Not your turn!"
            }

        # Roll dice
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        self.dice_result = (dice1, dice2)

        # Update board
        if self.board and "players" in self.board:
            for player in self.board["players"]:
                if player["id"] == player_id:
                    player["position"] = (player["position"] + dice1 + dice2) % 40
                    break

        result = {
            "type": C.TYPE_INFO,
            "event": C.EVENT_DICE_ROLLED,
            "dice": [dice1, dice2],
            "total": dice1 + dice2,
            "playerId": player_id,
            "board": self.get_board_state()
        }

        # Broadcast kết quả
        await self.broadcast(result)

        # Chuyển lượt và broadcast lượt mới
        self.next_turn()
        try:
            await self.broadcast({
                "type": C.TYPE_INFO,
                "event": C.EVENT_NEXT_TURN,
                "currentTurn": self.get_current_player_id()
            })
        except Exception as e:
            print(f"⚠️ Warning: failed to broadcast next turn: {e}")

        return result

    async def handle_buy_property(self, player_id: str) -> dict:
        """Xử lý mua property - TODO: implement thực tế"""
        # TODO: Implement buy property logic (kiểm tra vị trí, tiền, giá property, update money, properties)
        return {
            "type": C.TYPE_INFO,
            "message": "✅ Property bought!",
            "board": self.get_board_state()
        }

    def get_board_state(self) -> dict:
        """Lấy trạng thái board"""
        return self.board or {}

    def get_room_info(self) -> dict:
        """Lấy thông tin phòng"""
        return {
            "roomId": self.room_id,
            "roomName": self.room_name,
            "playerCount": len(self.players),
            "maxPlayers": self.max_players,
            "requiredPlayers": self.required_players,
            "state": self.state,
            "hostId": self.host_id,
            "players": [
                {
                    "id": pid,
                    "name": data['name'],
                    "isHost": data['is_host']
                }
                for pid, data in self.players.items()
            ]
        }

    async def broadcast(self, message: dict, send_timeout: float = 2.0):
        """Gửi message đến tất cả players trong phòng

        - Duyệt trên bản sao của items để tránh lỗi thay đổi dict khi lặp.
        - Sử dụng asyncio.wait_for để giới hạn thời gian send cho mỗi websocket.
        - Thu thập list disconnected để xóa sau khi gửi xong.
        """
        if not self.players:
            return

        disconnected_players: List[str] = []

        # Duyệt trên danh sách bản sao
        for player_id, player_data in list(self.players.items()):
            try:
                ws = player_data.get('websocket')
                if ws:
                    # giới hạn timeout khi gửi
                    try:
                        await asyncio.wait_for(ws.send(json.dumps(message)), timeout=send_timeout)
                    except asyncio.TimeoutError:
                        print(f"⚠️ Timeout sending to {player_data.get('name')} (ID: {player_id})")
                        disconnected_players.append(player_id)
                    except Exception as send_exc:
                        print(f"⚠️ Cannot send to {player_data.get('name')}: {send_exc}")
                        disconnected_players.append(player_id)
            except Exception as e:
                print(f"⚠️ Unexpected error while sending to {player_id}: {e}")
                disconnected_players.append(player_id)

        # Remove disconnected players after loop
        for player_id in disconnected_players:
            try:
                self.remove_player(player_id)
            except Exception as e:
                print(f"⚠️ Error removing disconnected player {player_id}: {e}")

    def mark_for_deletion(self):
        """Đánh dấu phòng để xóa"""
        self.marked_for_deletion = True
        self.state = C.STATE_FINISHED


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        # Optional lock if you plan to await while modifying rooms
        # self._lock = asyncio.Lock()

    def create_room(self, room_name, max_players=4, required_players=2):
        room_id = str(uuid.uuid4())[:8]
        room = GameRoom(room_id, room_name, max_players)
        self.rooms[room_id] = room
        print(f"✅ Tạo phòng {room_name} ({room_id}) với {max_players} người")
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        """Lấy phòng theo ID (trả None nếu phòng đã đánh dấu xóa)"""
        room = self.rooms.get(room_id)
        if room and getattr(room, 'marked_for_deletion', False):
            return None
        return room

    def remove_room(self, room_id: str):
        """Xóa phòng"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            # chỉ xóa khi trống hoặc đã được đánh dấu
            if len(room.players) == 0 or getattr(room, 'marked_for_deletion', False):
                del self.rooms[room_id]
                print(f"🗑️ Removed room: {room.room_name} (ID: {room_id})")

    def get_available_rooms(self) -> List[Room]:
        """Lấy danh sách phòng có thể tham gia"""
        available_rooms: List[Room] = []
        for room in self.rooms.values():
            if (len(room.players) < room.max_players and
                room.state in [C.STATE_WAITING, C.STATE_EMPTY] and
                not getattr(room, 'marked_for_deletion', False)):
                available_rooms.append(room)
        return available_rooms

    def cleanup_empty_rooms(self):
        """Dọn dẹp phòng trống - CHỈ xóa phòng đã trống lâu"""
        now = time.time()
        rooms_to_remove: List[str] = []

        for room_id, room in list(self.rooms.items()):
            # CHỈ xóa phòng trống và đã được đánh dấu xóa
            if (len(room.players) == 0 and
                getattr(room, 'marked_for_deletion', False) and
                hasattr(room, 'empty_since') and
                room.empty_since and
                (now - room.empty_since > 10)):
                rooms_to_remove.append(room_id)

        for room_id in rooms_to_remove:
            self.remove_room(room_id)
            print(f"🧹 Cleaned up empty room: {room_id}")

    async def periodic_cleanup(self):
        """Dọn dẹp phòng định kỳ"""
        while True:
            await asyncio.sleep(30)
            try:
                self.cleanup_empty_rooms()
                print(f"🔧 Room manager: {len(self.rooms)} rooms active")
            except Exception as e:
                print(f"⚠️ Error during periodic_cleanup: {e}")

    async def mark_room_for_deletion(self, room_id: str):
        """Đánh dấu phòng để xóa (khi game kết thúc hoặc host muốn đóng phòng)"""
        room = self.rooms.get(room_id)
        if room:
            room.marked_for_deletion = True
            # Thông báo cho tất cả players (broadcast an toàn vì broadcast duyệt trên bản sao)
            try:
                await room.broadcast({
                    "type": C.TYPE_INFO,
                    "message": "🏠 Phòng sẽ đóng sau khi tất cả người chơi rời đi"
                })
            except Exception as e:
                print(f"⚠️ Warning: failed to broadcast mark_room_for_deletion: {e}")
            print(f"🔧 Đánh dấu xóa phòng: {room.room_name}")
