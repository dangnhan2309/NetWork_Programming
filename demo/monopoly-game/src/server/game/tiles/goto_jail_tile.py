from .base_tile import BaseTile
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ..player import Player
    # Cần Board để nhất quán chữ ký on_land (thay vì Bank)
    from ..board import Board


class GoToJailTile(BaseTile):
    """
    Ô Go To Jail. Người chơi bị đưa thẳng vào tù khi vào ô này.
    """

    def __init__(self, tile_id: int, name: str, position: int):
        # ⚠️ Điều chỉnh tile_type thành "goto_jail" cho đúng chức năng
        super().__init__(tile_id, name, position, tile_type="goto_jail")

    def on_land(self, player: 'Player', board: 'Board') -> Dict[str, Any]:
        """
        Chỉ trả về instruction (lệnh) để GameManager đưa người chơi vào tù.
        Không thực hiện thay đổi trạng thái.

        Args:
            player: Người chơi vừa dừng lại.
            board: Board (được giữ để duy trì chữ ký hàm nhất quán).

        Returns:
            Dict chứa lệnh 'GOTO_JAIL'.
        """

        # 1. Trả về lệnh và thông điệp
        return {
            "event": "GOTO_JAIL",
            "message": f"{player.name} vừa dừng tại ô 'Go To Jail' và sẽ bị đưa vào tù ngay lập tức.",
            "data": {
                # Thông tin tối thiểu cần thiết, GameManager sẽ tự tìm vị trí tù
                "player_id": player.id,
            }
        }

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển tile thành dict gửi client."""
        base = super().to_dict()
        base.update({
            "type": self.tile_type,
            "name": self.name,
        })
        return base