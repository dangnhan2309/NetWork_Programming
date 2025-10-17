# file: game/tiles/property_tile.py
from .base_tile import BaseTile
from typing import TYPE_CHECKING
from ..properties import ColorGroupProperty

if TYPE_CHECKING:
    from ..player import Player
    from ..board import Board


class PropertyTile(BaseTile):
    """Đại diện cho ô đất có màu (Color Group Property)."""

    def __init__(self, tile_id, name, position, colour, properties_obj: ColorGroupProperty):
        super().__init__(tile_id, name, position, tile_type="property")
        self.properties = properties_obj
        self.price = self.properties.purchase_price
        self.colour = colour
        self.owner = self.properties.owner  # Player ID hoặc None

    def get_owner_id(self, bank_service) -> int | None:
        """Truy vấn Bank để tìm ID của chủ sở hữu ô đất này."""
        return bank_service.properties_owned.get(self.tile_id)

    def on_land(self, player: 'Player', board: 'Board'):
        """
        Khi người chơi dừng tại ô đất:
        - Nếu chưa có chủ → Gợi ý mua.
        - Nếu là của chính mình → Không hành động.
        - Nếu của người khác → Trả tiền thuê.
        """
        owner_id = self.get_owner_id(board.bank)
        owner = board.get_player_by_id(owner_id) if owner_id is not None else None

        # 🟩 1. Ô đất chưa có chủ
        if owner_id is None:
            return {
                "event": "land_on_property",
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

        # 🟨 2. Chính chủ
        elif owner_id == player.id:
            return {
                "event": "land_on_property",
                "message": f"{player.name} landed on their own property ({self.name}).",
                "effect": {
                    "action": "none",
                    "data": {
                        "property_id": self.tile_id
                    }
                },
                "data": self.to_dict()
            }

        # 🟥 3. Của người khác → Trả tiền thuê
        else:
            rent = self.properties.calculate_rent()
            return {
                "event": "land_on_property",
                "message": f"{player.name} must pay ${rent} rent to {owner.name} for {self.name}.",
                "effect": {
                    "action": "pay_rent",
                    "data": {
                        "property_id": self.tile_id,
                        "owner": owner,
                        "rent": rent
                    }
                },
                "data": self.to_dict()
            }

    def to_dict(self):
        """Serialize tile info (được gửi về client)."""
        base = super().to_dict()
        base.update({
            "price": self.price,
            "rent": self.properties.calculate_rent(),
            "owner_id": self.properties.owner,
            "colour": self.colour
        })
        return base
