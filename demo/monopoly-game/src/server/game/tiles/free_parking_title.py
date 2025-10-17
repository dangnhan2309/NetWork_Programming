# game/tiles/free_parking_tile.py
from .base_tile import BaseTile
from typing import TYPE_CHECKING, Dict, Any
from ...network.packet_builder import PacketBuilder

if TYPE_CHECKING:
    from ..player import Player
    from ..Bank import Bank


class FreeParkingTile(BaseTile):
    """
    Ô Free Parking (Bãi đậu xe miễn phí).
    - Theo luật gốc: không có tác dụng gì.
    - Theo luật tùy chọn (House Rule): nhận tiền từ quỹ Free Parking Pool.
    """

    def __init__(self, tile_id: int, name: str, position: int):
        super().__init__(tile_id, name, position, tile_type="free_parking")

    def on_land(self, player: 'Player', bank_service: 'Bank') -> Dict[str, Any]:
        """
        Khi người chơi dừng lại trên ô Free Parking:
        - Nếu pool có tiền: nhận toàn bộ và pool đặt lại 0.
        - Nếu trống: chỉ hiển thị thông báo.
        """

        pool_amount = getattr(bank_service, "free_parking_pool", 0)
        collected_amount = 0

        # 🏦 Nếu có tiền trong quỹ
        if pool_amount > 0:
            collected_amount = bank_service.pay_free_parking(player)

            # Gói tin cập nhật số dư
            balance_packet = PacketBuilder.update_balance(
                room_id=getattr(bank_service, "room_id", None),
                player_id=player.id,
                balance=player.balance
            )

            # Trả về event JSON chuẩn hóa
            return {
                "event": "FREE_PARKING_COLLECT",
                "message": f"{player.name} collected ${collected_amount} from Free Parking!",
                "data": {
                    "tile_id": self.tile_id,
                    "tile_name": self.name,
                    "tile_type": self.tile_type
                },
                "effect": {
                    "amount": collected_amount,
                    "pool_cleared": True
                },
                "packets": [balance_packet]
            }

        # 🚗 Nếu pool trống
        return {
            "event": "FREE_PARKING_EMPTY",
            "message": f"{player.name} stopped at Free Parking. The pool is empty.",
            "data": {
                "tile_id": self.tile_id,
                "tile_name": self.name,
                "tile_type": self.tile_type
            },
            "effect": {
                "amount": 0,
                "pool_cleared": False
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
