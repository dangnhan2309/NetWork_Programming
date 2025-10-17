from typing import Dict, TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .player import Player
    from .board import Board
    from .tiles.base_tile import BaseTile
    from .tiles.property_tile import PropertyTile


class Bank:
    """
    Quản lý tài chính trung tâm trong Monopoly:
    - Theo dõi tiền của từng người chơi
    - Quản lý giao dịch với Bank, giữa các Player
    - Quản lý sở hữu Property, nhà, khách sạn
    """

    def __init__(self):
        # 💰 Quỹ của Bank và người chơi
        self.cash_pool: int = 100_000
        self.free_parking_pool: int = 0
        self.player_balances: Dict[str, int] = {}

        # 🏠 Sở hữu tài sản
        self.properties_owned: Dict[int, str] = {}  # property_id -> player_id
        self.available_houses: int = 32
        self.available_hotels: int = 12

    # ======================================================
    # 🧾 QUẢN LÝ NGƯỜI CHƠI
    # ======================================================
    def register_player(self, player: 'Player', initial_balance: int = 1500):
        """Thêm người chơi mới vào hệ thống Bank."""
        if player.id not in self.player_balances:
            self.player_balances[player.id] = initial_balance

    def get_balance(self, player: 'Player') -> int:
        """Lấy số dư của người chơi."""
        return self.player_balances.get(player.id, 0)

    # ======================================================
    # 💸 GIAO DỊCH VỚI BANK
    # ======================================================
    def pay_player(self, player: 'Player', amount: int) -> bool:
        """Bank trả tiền cho người chơi (ví dụ: qua ô GO)."""
        if self.cash_pool >= amount:
            self.cash_pool -= amount
            self.player_balances[player.id] += amount
            return True
        return False

    def pay_bank(self, player: 'Player', amount: int) -> bool:
        """Người chơi trả tiền cho Bank (thuế, phạt, ...)."""
        current_balance = self.get_balance(player)
        if current_balance >= amount:
            self.player_balances[player.id] -= amount
            self.cash_pool += amount
            return True
        else:
            # Người chơi phá sản
            self.cash_pool += current_balance
            self.player_balances[player.id] = 0
            player.is_bankrupt = True
            return False

    # ======================================================
    # 🔁 GIAO DỊCH GIỮA NGƯỜI CHƠI
    # ======================================================
    def transfer_between_players(self, sender: 'Player', receiver: 'Player', amount: int) -> Dict:
        """Chuyển tiền giữa hai người chơi (trả tiền thuê, nợ)."""
        sender_balance = self.get_balance(sender)
        if sender_balance >= amount:
            self.player_balances[sender.id] -= amount
            self.player_balances[receiver.id] += amount
            return {"success": True, "message": f"{sender.name} paid ${amount} to {receiver.name}."}
        else:
            # Phá sản
            self.player_balances[sender.id] = 0
            sender.is_bankrupt = True
            if sender_balance > 0:
                self.player_balances[receiver.id] += sender_balance
            return {"success": False, "message": f"{sender.name} went bankrupt paying {receiver.name} ${sender_balance}."}

    # ======================================================
    # 🅿️ FREE PARKING
    # ======================================================
    def collect_tax_or_fee(self, player: 'Player', amount: int):
        """Thu tiền vào Free Parking Pool."""
        self.player_balances[player.id] -= amount
        self.free_parking_pool += amount

    def pay_free_parking(self, player: 'Player'):
        """Trả toàn bộ tiền trong Free Parking cho người chơi."""
        collected = self.free_parking_pool
        self.player_balances[player.id] += collected
        self.free_parking_pool = 0
        return collected

    # ======================================================
    # 🏠 PROPERTY MANAGEMENT
    # ======================================================
    def buy_property(self, player: 'Player', tile: 'PropertyTile') -> bool:
        """
        Người chơi mua Property từ Bank.
        - Giảm tiền của người chơi
        - Gán quyền sở hữu trong Bank
        """
        price = tile.price
        if self.get_balance(player) >= price:
            self.player_balances[player.id] -= price
            self.properties_owned[tile.tile_id] = str(player.id)
            tile.owner = player.id
            return True
        return False

    def set_property_owner(self, property_id: int, player_id: int):
        """Gán property cho người chơi."""
        self.properties_owned[property_id] = str(player_id)

    def reset_property_owner(self, player_id: int):
        """Xóa toàn bộ property của người chơi (phá sản)."""
        self.properties_owned = {pid: owner for pid, owner in self.properties_owned.items() if owner != str(player_id)}

    def get_properties_by_owner(self, player_id: int, board: 'Board') -> List['BaseTile']:
        """Trả danh sách Tile mà player sở hữu."""
        owned_tile_ids = [pid for pid, owner in self.properties_owned.items() if owner == str(player_id)]
        return [tile for tile in board.tiles if tile.tile_id in owned_tile_ids]

    def get_owner_id(self, tile_id: int) -> Optional[int]:
        """Truy vấn người sở hữu của một tile."""
        return self.properties_owned.get(tile_id)

    def remove_property_player_sell(self, tile_id: int, player_id: str) -> bool:
        """
        Xóa quyền sở hữu của người chơi đối với một ô đất cụ thể khi người chơi bán.

        Args:
            tile_id: ID của ô đất bị bán.
            player_id: ID của người chơi đang bán (dùng để xác thực).

        Returns:
            True nếu quyền sở hữu được xóa thành công, False nếu tile không tồn tại
            hoặc không thuộc về người chơi đó.
        """
        current_owner_id = self.properties_owned.get(tile_id)

        # 1. Kiểm tra xem ô đất có tồn tại không
        if current_owner_id is None:
            # Ghi log: Ô đất không có chủ hoặc ID không hợp lệ.
            print(f"Error: Tile {tile_id} is not currently owned.")
            return False

        # 2. Kiểm tra xem người bán có phải là chủ sở hữu hiện tại không
        if current_owner_id != player_id:
            # Ghi log: Người chơi không phải là chủ sở hữu hợp lệ.
            print(f"Error: Player {player_id} does not own tile {tile_id}. Current owner: {current_owner_id}")
            return False

        # 3. Xóa quyền sở hữu
        try:
            del self.properties_owned[tile_id]
            print(f"Success: Tile {tile_id} ownership removed.")
            return True
        except KeyError:
            # Nên được bắt bởi kiểm tra ban đầu, nhưng thêm vào để đảm bảo an toàn
            return False

    # ======================================================
    # 🏗️ NHÀ & KHÁCH SẠN
    # ======================================================
    def houses_available(self) -> int:
        """Trả về số lượng nhà còn lại."""
        return self.available_houses

    def hotels_available(self) -> int:
        """Trả về số lượng khách sạn còn lại."""
        return self.available_hotels

    def build_house(self, player: 'Player', tile: 'PropertyTile') -> bool:
        """Xây 1 nhà trên property."""
        if self.available_houses > 0 and tile.owner == player.id:
            self.available_houses -= 1
            tile.properties.houses += 1
            return True
        return False

    def build_hotel(self, player: 'Player', tile: 'PropertyTile') -> bool:
        """Xây khách sạn (sau khi đủ 4 nhà)."""
        if tile.properties.houses == 4 and self.available_hotels > 0:
            self.available_hotels -= 1
            self.available_houses += 4  # Trả lại 4 nhà
            tile.properties.houses = 0
            tile.properties.has_hotel = True
            return True
        return False
