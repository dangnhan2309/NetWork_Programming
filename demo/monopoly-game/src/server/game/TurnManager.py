# game/TurnManager.py

from typing import List, Optional
from .player import Player

class TurnManager:
    """
    Quản lý lượt chơi:
    - Xác định người chơi hiện tại
    - Chuyển lượt kế tiếp
    - Bỏ qua người chơi đã phá sản
    """

    def __init__(self, players: List[Player]):
        self.   players: List[Player] = players
        self.current_index: int = 0

    # ----------------------------------------
    # Lấy người chơi hiện tại
    # ----------------------------------------
    def get_current_player(self) -> Optional[Player]:
        """Trả về player đang đến lượt, bỏ qua người chơi phá sản"""
        active_players = [p for p in self.players if not p.is_bankrupt]
        if not active_players:
            return None
        # Nếu current_index vượt giới hạn active_players, reset về 0
        self.current_index %= len(active_players)
        return active_players[self.current_index]

    # ----------------------------------------
    # Chuyển lượt
    # ----------------------------------------
    def next_turn(self) -> Optional[Player]:
        """Chuyển sang lượt người chơi tiếp theo"""
        active_players = [p for p in self.players if not p.is_bankrupt]
        if not active_players:
            return None

        # Tăng chỉ số để vòng tiếp theo
        self.current_index = (self.current_index + 1) % len(active_players)
        return self.get_current_player()

    # ----------------------------------------
    # Đồng bộ danh sách player
    # ----------------------------------------
    def update_players(self, players: List[Player]):
        """Cập nhật danh sách người chơi (ví dụ khi có người rời/phá sản)"""
        self.players = players
        # Reset index nếu cần
        self.current_index %= len(players)

    # ----------------------------------------
    # Serialize trạng thái
    # ----------------------------------------
    def serialize(self) -> dict:
        return {
            "current_index": self.current_index,
            "current_player_id": self.get_current_player().id if self.get_current_player() else None,
            "active_players": [p.id for p in self.players if not p.is_bankrupt]
        }
