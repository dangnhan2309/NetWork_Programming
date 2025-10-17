from ..card_manager2 import CardManager
from .base_tile import BaseTile
from ...network.packet_builder import PacketBuilder


class CommunityTile(BaseTile):
    def __init__(self, tile_id, name, position, deck="community"):
        super().__init__(tile_id, name, position, "community")
        self.deck_type = deck
        self.manager = CardManager()

    def on_land(self, player, board):
        """
        Khi người chơi dừng tại ô Chance:
        1️⃣ Rút một thẻ ngẫu nhiên
        2️⃣ Gửi packet thông báo rút thẻ
        3️⃣ Áp dụng hiệu ứng thẻ
        4️⃣ Trả về event chuẩn hóa
        """

        # 1️⃣ Rút thẻ từ bộ bài Chance
        card = self.manager.draw_card(self.deck_type)

        # 2️⃣ Tạo gói tin thông báo rút thẻ (để gửi qua network)
        draw_packet = PacketBuilder.draw_card(
            room_id=board.room_id,              # board có thể giữ room_id hoặc bạn truyền từ GameManager
            player_id=player.id,
            card_type=self.deck_type,
            card_data=card
        )

        # ⚠️ Không gửi ở đây — việc gửi packet do GameManager chịu trách nhiệm
        # Chỉ cần trả về cho GameManager biết có gói tin nào cần gửi

        # 3️⃣ Áp dụng hiệu ứng của thẻ (thay đổi player/balance/position, v.v.)
        result = self.manager.apply_effect(card, player, board, board.players)

        # 4️⃣ Trả về event để GameManager xử lý và gửi đi
        return {
            "event": "DRAW_CARD",
            "message": f"{player.name} drew a Community card: {card["text"]}",
            "effect": result,   # hiệu ứng cụ thể: {"move_to": 24, "amount": -50, ...}
            "data": {
                "tile_id": self.tile_id,
                "tile_name": self.name,
                "tile_type": self.tile_type,
                "card_type": self.deck_type,
                "card_info": card,
            },
            "packets": [draw_packet]  # Gợi ý để GameManager gửi trước khi apply effect
        }

    def to_dict(self):
        """Trả về thông tin tile để client hiển thị"""
        base = super().to_dict()
        base.update({
            "deck_type": self.deck_type
        })
        return base