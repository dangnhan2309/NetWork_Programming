# server/game_manager.py
# Quản lý lượt chơi & trạng thái game; có thể broadcast GAME_STATE qua ServerNetwork.

import random
from typing import List, Optional, TYPE_CHECKING, Dict, Any
from .player import Player               # → Lớp người chơi
from .board import Board                 # → Renderer/board logic (get_tile / render_ascii)

if TYPE_CHECKING:
    from .network import ServerNetwork   # → Chỉ dùng cho type hint (tránh vòng import runtime)

class GameManager:
    """
    → Điều phối game:
      - get_state(): gom state ở định dạng mà client/Board cần
      - sync_state(): phát GAME_STATE qua network
      - play_turn(): tung xúc xắc, move, handle_tile, rồi sync
    """

    def __init__(self, players: List[Player], network: Optional["ServerNetwork"] = None):  # → Khởi tạo GM
        self.players = players           # → Danh sách Player
        self.board = Board()             # → Bàn cờ/renderer
        self.current_turn = 0            # → Lượt hiện tại (index trong players)
        self.network = network           # → Tham chiếu ServerNetwork để broadcast (có thể None)

    # ---------- STATE cho client ----------
    def _pos_of(self, p: Player) -> int:  # → Lấy chỉ số ô 0..39 của player
        if hasattr(p, "position_index"):
            try: return int(getattr(p, "position_index"))
            except: return 0
        if hasattr(p, "position"):
            try: return int(getattr(p, "position"))
            except: return 0
        return 0

    def get_state(self) -> dict:  # → Trả về state theo format renderer cần
        players_state = [{"nick": getattr(p, "name", "P"), "pos": self._pos_of(p)} for p in self.players]
        ownership: Dict[int, str] = {}            # → {tileIndex: ownerNick}, nếu có hệ đất đai map vào đây
        buildings: Dict[int, Dict[str, Any]] = {} # → {tileIndex: {houses, hotel}}, nếu có xây dựng map vào đây
        return {"players": players_state, "ownership": ownership, "buildings": buildings}

    def sync_state(self, reason: str = "") -> None:  # → Phát GAME_STATE tới tất cả clients
        if self.network:
            self.network.broadcast({"type": "GAME_STATE", "reason": reason, "state": self.get_state()})

    # ---------- Lượt chơi ----------
    def roll_dice(self):  # → Tung 2 viên, trả (tổng, có double không)
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        return d1 + d2, (d1 == d2)

    def next_turn(self):  # → Chuyển lượt sang người tiếp theo
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def play_turn(self):  # → Chạy 1 lượt: roll → move → handle_tile → sync → (double thì được đi tiếp)
        player = self.players[self.current_turn]
        steps, is_double = self.roll_dice()
        player.move(steps)                                              # → Player phải cộng vị trí 0..39

        idx = self._pos_of(player)
        tile = self.board.get_tile(idx) if hasattr(self.board, "get_tile") else {}  # → Lấy thông tin ô hiện tại
        self.handle_tile(player, tile)                                  # → Xử lý logic ô (thuế, tù, chance, property...)

        self.sync_state("after_turn")                                   # → Phát state sau lượt
        if not is_double:
            self.next_turn()

    def handle_tile(self, player: Player, tile: dict):  # → Logic xử lý ô (m có thể mở rộng)
        t = tile.get("type")
        if t == "tax" and hasattr(player, "pay_tax"):
            player.pay_tax(int(tile.get("amount", 0)))
        elif t == "jail" and hasattr(player, "jail_time"):
            player.jail_time()
        elif t == "chance" and hasattr(player, "draw_lucky_card"):
            player.draw_lucky_card()
        elif t == "property":
            # → Chỗ này m có thể thêm mua/thuê… ( thêm luật vào nếu thiếu)
            pass
        # ... thêm loại ô khác nếu muốn