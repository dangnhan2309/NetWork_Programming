# file: game/tiles/utility_tile.py

from .base_tile import BaseTile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..player import Player
    from ..board import Board
    from ..Bank import Bank


class UtilityTile(BaseTile):
    """Đại diện cho ô Công Ty Tiện Ích (Điện lực, Nước) trên bàn cờ."""

    def __init__(self, tile_id: int, name: str, position: int, properties_obj):
        super().__init__(tile_id, name, position, tile_type="utility")
        self.properties = properties_obj
        self.price = self.properties.purchase_price

    def calculate_rent(self, board: 'Board', owner_id: int, dice_roll: int) -> int:
        """Tính tiền thuê dựa trên số nút xúc xắc (dice_roll)."""
        owner_properties = board.bank.get_properties_by_owner(owner_id)
        utility_count = sum(
            1 for tile in owner_properties
            if tile.tile_type == "utility"
        )

        multiplier_tiers = {1: 4, 2: 10}
        multiplier = multiplier_tiers.get(utility_count, 4)
        return multiplier * dice_roll

    def on_land(self, player: 'Player', board: 'Board', last_dice_roll: int = 0):
        """
        Khi người chơi dừng tại Utility Tile:
        - Nếu chưa có chủ → Gợi ý mua.
        - Nếu là của chính mình → Không hành động.
        - Nếu của người khác → Tính tiền thuê.
        """
        owner_id = board.bank.get_owner_id(self.tile_id)
        owner = board.get_player_by_id(owner_id) if owner_id is not None else None

        # 🟩 1. Chưa có chủ
        if owner_id is None:
            return {
                "event": "land_on_utility",
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
                "event": "land_on_utility",
                "message": f"{player.name} landed on their own utility ({self.name}).",
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
            if last_dice_roll == 0:
                raise ValueError("Cannot calculate Utility rent without last_dice_roll value.")

            rent_amount = self.calculate_rent(board, owner_id, last_dice_roll)
            return {
                "event": "land_on_utility",
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

    def to_dict(self):
        base = super().to_dict()
        owner_id = self.properties.owner
        base.update({
            "price": self.price,
            "owner_id": owner_id
        })
        return base
