from typing import Dict, TYPE_CHECKING
from .Bank import Bank
# Import PacketBuilder từ vị trí đã định nghĩa của bạn
from ..network.packet_builder import PacketBuilder


if TYPE_CHECKING:
    from .tiles.property_tile import PropertyTile
class Player:
    """
    Đại diện cho một người chơi trong Monopoly.
    """

    def __init__(self, player_id: str, name: str, bank_service: Bank, room_id: str, initial_balance: int = 1500):
        self.id = player_id
        self.name = name
        self.position = 0
        self.in_jail = False
        self.jail_turns = 0
        self.is_bankrupt = False
        self.has_rolled_and_moved = False
        self.consecutive_doubles = 0
        self.room_id = room_id

        # 🔑 SOURCE OF TRUTH: Set chứa ID của các ô đất người chơi sở hữu

        self.bank = bank_service
        self.bank.register_player(self, initial_balance)

        # 💥 Thêm PacketBuilder để tạo JSON packet hành động
        # Lưu ý: PacketBuilder nên là static hoặc được truyền vào
        # Tôi sẽ để nó là instance tạm thời, nhưng dùng @classmethod cho các hàm là tốt nhất.
        self.packet_builder = PacketBuilder()

    # ======================================================
    # 💰 TIỀN VÀ GIAO DỊCH
    # ======================================================
    @property
    def balance(self) -> int:
        """Lấy số dư từ Bank."""
        return self.bank.get_balance(self)




    # ======================================================
    # 🏠 TÀI SẢN (Dùng self.owned_tiles)
    # ======================================================

    # ======================================================
    # SERIALIZATION
    # ======================================================
    def serialize(self) -> Dict:
        """Chuẩn hóa dữ liệu người chơi để gửi qua mạng hoặc lưu trữ."""
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "balance": self.balance,
            "owned_tiles": list(self.owned_tiles),  # Convert Set to List để JSON hóa
            "in_jail": self.in_jail,
            "jail_turns": self.jail_turns,
            "is_bankrupt": self.is_bankrupt
        }

    def __repr__(self):
        return f"<Player {self.name} (${self.balance}) pos={self.position}>"
