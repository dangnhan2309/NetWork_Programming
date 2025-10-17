# game/tiles/jail_tile.py
from .base_tile import BaseTile
from ..network.packet_builder import PacketBuilder  # import thêm

class JailTile(BaseTile):
    def __init__(self, tile_id, name, position):
        super().__init__(tile_id, name, position, tile_type="jail")

    def on_land(self, player, board):
        """
        Khi người chơi dừng tại ô Jail.
        - Nếu đang ở tù -> chỉ chờ (không được đi)
        - Nếu không ở tù -> chỉ là khách ghé thăm
        """
        if player.is_in_jail:
            # Người chơi vẫn đang bị giam
            return PacketBuilder.info_message(
                event="jail_wait",
                message=f"{player.name} vẫn đang ở trong tù và phải chờ lượt kế tiếp."
            )
        else:
            # Người chơi chỉ đi qua / ghé thăm
            return PacketBuilder.info_message(
                event="just_visiting",
                message=f"{player.name} chỉ đang ghé thăm nhà tù."
            )

    def to_dict(self):
        """
        Có thể mở rộng: chứa danh sách người chơi hiện đang ở trong Jail.
        """
        base = super().to_dict()
        # có thể thêm:
        # base["players_in_jail"] = [p.name for p in board.get_players_in_jail()]
        return base
