# file: game/tiles/railroad_tile.py

from .base_tile import BaseTile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..player import Player
    from ..Bank import Bank
    from ..board import Board


class RailroadTile(BaseTile):
    """Đại diện cho 4 ô Ga Tàu Hỏa trên bàn cờ (Railroad)."""

    def __init__(self, tile_id: int, name: str, position: int, properties_obj):
        super().__init__(tile_id, name, position, tile_type="railroad")
        self.properties = properties_obj
        self.price = self.properties.purchase_price

    # ---------------------------------------------------------------------
    # 🔢 TÍNH TIỀN THUÊ
    # ---------------------------------------------------------------------
    def calculate_rent(self, board: 'Board', owner_id: int) -> int:
        """
        Tiền thuê dựa trên số lượng Railroad mà chủ sở hữu nắm giữ.
        """
        owner_properties = board.bank.get_properties_by_owner(owner_id)
        railroad_count = sum(
            1 for tile in owner_properties if tile.tile_type == "railroad"
        )

        rent_tiers = {1: 25, 2: 50, 3: 100, 4: 200}
        return rent_tiers.get(railroad_count, 25)

    # ---------------------------------------------------------------------
    # 🚂 KHI NGƯỜI CHƠI DỪNG LẠI TRÊN GA
    # ---------------------------------------------------------------------
    def on_land(self, player: 'Player', board: 'Board'):
        """
        Chỉ trả về event mô tả hành động cần thực hiện.
        Không thực thi trực tiếp việc mua bán hay chuyển tiền.
        """
        owner_id = board.bank.get_owner_id(self.tile_id)
        owner = board.get_player_by_id(owner_id) if owner_id is not None else None

        # 🟩 1️⃣ Chưa có chủ → Gợi ý mua
        if owner_id is None:
            return {
                "event": "land_on_railroad",
                "message": f"{player.name} can buy {self.name} for ${self.price}.",
                "effect": {
                    "action": "buy",
                    "data": {
                        "property_id": self.tile_id,
                        "price": self.price
                    }
                },
                "data": self.to_dict()
            }

        # 🟨 2️⃣ Người chơi là chủ → Không làm gì
        elif owner_id == player.id:
            return {
                "event": "land_on_railroad",
                "message": f"{player.name} landed on their own railroad ({self.name}).",
                "effect": {
                    "action": "none",
                    "data": {
                        "property_id": self.tile_id
                    }
                },
                "data": self.to_dict()
            }

        # 🟥 3️⃣ Ô của người khác → Trả tiền thuê
        else:
            rent_amount = self.calculate_rent(board, owner_id)
            return {
                "event": "land_on_railroad",
                "message": f"{player.name} must pay ${rent_amount} rent to {owner.name} for {self.name}.",
                "effect": {
                    "action": "pay_rent",
                    "data": {
                        "property_id": self.tile_id,
                        "owner": owner,
                        "rent": rent_amount
                    }
                },
                "data": self.to_dict()
            }

    # ---------------------------------------------------------------------
    # 🧾 SERIALIZE
    # ---------------------------------------------------------------------
    def to_dict(self):
        """Chuyển đối tượng thành dict để gửi về client."""
        base = super().to_dict()
        base.update({
            "price": self.price,
            "owner_id": getattr(self.properties, "owner", None)
        })
        return base
