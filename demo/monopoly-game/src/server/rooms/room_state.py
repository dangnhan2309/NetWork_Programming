from typing import Dict, List, Optional
import random

# ==========================
#  Stub classes (định nghĩa placeholder)
# ==========================

class Player:
    def __init__(self, player_id: str, name: str):
        self.player_id = player_id
        self.name = name
        self.position = 0
        self.balance = 1500
        self.assets = []

    def move(self, steps: int) -> int:
        """Di chuyển người chơi trên bàn cờ"""
        return self.position  # placeholder

    def buy_property(self, property_id: str) -> bool:
        """Mua tài sản, trả về True nếu thành công"""
        return True  # placeholder

    def pay(self, amount: int, receiver=None) -> bool:
        """Thanh toán số tiền cho người khác hoặc hệ thống"""
        return True  # placeholder

    def __repr__(self):
        return f"Player({self.name}, pos={self.position}, balance={self.balance})"


class Board:
    def __init__(self):
        self.tiles = []

    def get_tile(self, position: int) -> Dict:
        """Trả về thông tin ô trên bàn cờ"""
        return {}  # placeholder

    def next_position(self, current_pos: int, steps: int) -> int:
        """Tính vị trí tiếp theo"""
        return (current_pos + steps) % len(self.tiles) if self.tiles else 0


# ==========================
#  RoomState Class
# ==========================

class RoomState:
    """
    Quản lý trạng thái game trong một phòng:
    - Danh sách người chơi
    - Trạng thái lượt
    - Bàn cờ
    - Vòng chơi, người thắng/thua
    """

    def __init__(self, room_id: str, board: Optional[Board] = None):
        self.room_id = room_id
        self.board = board or Board()
        self.players: Dict[str, Player] = {}
        self.turn_order: List[str] = []
        self.current_turn_index: int = 0
        self.round_number: int = 1
        self.active: bool = False
        self.winner: Optional[str] = None

    # ========== Player Management ==========

    def add_player(self, player_id: str, name: str) -> bool:
        """Thêm người chơi vào phòng"""
        if player_id in self.players:
            return False
        self.players[player_id] = Player(player_id, name)
        self.turn_order.append(player_id)
        return True

    def remove_player(self, player_id: str):
        """Xóa người chơi khỏi phòng"""
        if player_id in self.players:
            del self.players[player_id]
            if player_id in self.turn_order:
                self.turn_order.remove(player_id)

    # ========== Game Flow ==========

    def start_game(self):
        """Bắt đầu ván chơi"""
        if len(self.players) < 2:
            raise ValueError("Cần ít nhất 2 người chơi để bắt đầu")
        self.active = True
        self.current_turn_index = 0
        self.round_number = 1
        self.winner = None

    def next_turn(self):
        """Chuyển sang lượt tiếp theo"""
        if not self.active:
            return
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        if self.current_turn_index == 0:
            self.round_number += 1

    def get_current_player(self) -> Optional[Player]:
        """Lấy người chơi hiện tại"""
        if not self.turn_order:
            return None
        current_id = self.turn_order[self.current_turn_index]
        return self.players.get(current_id)

    # ========== Game Logic ==========

    def roll_dice(self) -> int:
        """Xúc xắc"""
        return random.randint(1, 6)

    def player_move(self, player_id: str):
        """Xử lý di chuyển người chơi"""
        player = self.players.get(player_id)
        if not player:
            return
        steps = self.roll_dice()
        new_pos = self.board.next_position(player.position, steps)
        player.move(steps)
        return {"player": player_id, "steps": steps, "new_pos": new_pos}

    def player_buy(self, player_id: str, property_id: str):
        """Xử lý người chơi mua tài sản"""
        player = self.players.get(player_id)
        if player:
            success = player.buy_property(property_id)
            return success
        return False

    # ========== State & Info ==========

    def get_state(self) -> Dict:
        """Lấy toàn bộ trạng thái phòng"""
        return {
            "room_id": self.room_id,
            "players": {pid: vars(p) for pid, p in self.players.items()},
            "current_turn": self.turn_order[self.current_turn_index] if self.turn_order else None,
            "round_number": self.round_number,
            "active": self.active,
            "winner": self.winner,
        }

    def reset(self):
        """Đặt lại trạng thái phòng"""
        self.active = False
        self.round_number = 1
        self.current_turn_index = 0
        self.winner = None
        for player in self.players.values():
            player.position = 0
            player.balance = 1500
            player.assets.clear()

    # ========== End Game ==========

    def check_winner(self):
        """Kiểm tra điều kiện thắng"""
        if len(self.players) == 1:
            self.winner = next(iter(self.players.keys()))
            self.active = False
        elif all(p.balance <= 0 for p in self.players.values()):
            self.winner = max(self.players.values(), key=lambda p: p.balance).player_id
            self.active = False

    def __repr__(self):
        return f"<RoomState {self.room_id} | Round {self.round_number} | Players {len(self.players)}>"

