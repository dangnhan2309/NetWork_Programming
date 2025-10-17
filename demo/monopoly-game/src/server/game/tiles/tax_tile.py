# game/tiles/tax_tile.py
from .base_tile import BaseTile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..player import Player
    from ..board import Board


class TaxTile(BaseTile):
    def __init__(self, tile_id, name, position, tax_amount):
        super().__init__(tile_id, name, position, tile_type="tax")
        self.tax_amount = tax_amount

    def on_land(self, player: 'Player', board: 'Board'):
        """
        Không trừ tiền trực tiếp ở đây.
        Chỉ trả về event để GameManager xử lý và gửi về client.
        """
        return {
            "event": "TAX_PAYMENT",
            "message": f"{player.name} must pay ${self.tax_amount} in taxes.",
            "effect": {
                "type": "MONEY_CHANGE",
                "amount": -self.tax_amount,
                "target": player.name,
                "recipient": "Bank",
            },
            "data": {
                "tile_id": self.tile_id,
                "tile_name": self.name,
                "tile_type": self.tile_type,
                "tax_amount": self.tax_amount
            }
        }

    def to_dict(self):
        base = super().to_dict()
        base.update({"tax_amount": self.tax_amount})
        return base
