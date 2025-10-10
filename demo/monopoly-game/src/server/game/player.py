"""
Player class for Monopoly
----------------------------------
Đại diện cho một người chơi trong Monopoly game.
Quản lý tiền, vị trí, tài sản, lượt, và các hành động cơ bản.
"""

from typing import Dict, List, Optional


class Player:
    def __init__(self, player_id: str, name: str, starting_money: int = 1500):
        self.id = player_id
        self.name = name
        self.money = starting_money
        self.position = 0
        self.properties: List[int] = []
        self.in_jail = False
        self.jail_turns = 0
        self.bankrupt = False
        self.turn_active = False

    # ======================================
    # 🧭 Movement
    # ======================================

    def move(self, steps: int, board_size: int = 40) -> int:
        """Di chuyển người chơi trên board"""
        if self.in_jail:
            return self.position

        old_pos = self.position
        self.position = (self.position + steps) % board_size

        # Nếu vượt qua "GO" -> +200$
        if self.position < old_pos:
            self.money += 200

        return self.position

    # ======================================
    # 💰 Money Management
    # ======================================

    def pay(self, amount: int, receiver: Optional["Player"] = None) -> bool:
        """Trả tiền cho người chơi khác hoặc ngân hàng"""
        if self.money < amount:
            self.money = 0
            self.bankrupt = True
            return False

        self.money -= amount
        if receiver:
            receiver.money += amount
        return True

    def earn(self, amount: int):
        """Nhận tiền (từ GO, Chance, v.v.)"""
        self.money += amount

    def is_bankrupt(self) -> bool:
        """Kiểm tra người chơi đã phá sản chưa"""
        return self.bankrupt or self.money <= 0

    # ======================================
    # 🏠 Property Management
    # ======================================

    def add_property(self, tile_id: int):
        """Thêm tài sản vào danh sách sở hữu"""
        if tile_id not in self.properties:
            self.properties.append(tile_id)

    def remove_property(self, tile_id: int):
        """Xóa tài sản khi bán hoặc phá sản"""
        if tile_id in self.properties:
            self.properties.remove(tile_id)

    def reset_properties(self):
        """Xóa toàn bộ tài sản"""
        self.properties.clear()

    # ======================================
    # ⏱ Jail & Turn Management
    # ======================================

    def send_to_jail(self, jail_pos: int):
        """Đưa người chơi vào tù"""
        self.position = jail_pos
        self.in_jail = True
        self.jail_turns = 3

    def process_jail_turn(self):
        """Xử lý 1 lượt trong tù"""
        if self.in_jail:
            self.jail_turns -= 1
            if self.jail_turns <= 0:
                self.in_jail = False

    def start_turn(self):
        """Kích hoạt lượt chơi"""
        self.turn_active = True

    def end_turn(self):
        """Kết thúc lượt chơi"""
        self.turn_active = False

    # ======================================
    # 🧾 Serialization
    # ======================================

    def to_dict(self) -> Dict:
        """Chuyển sang dict để gửi qua network"""
        return {
            "id": self.id,
            "name": self.name,
            "money": self.money,
            "position": self.position,
            "properties": self.properties,
            "in_jail": self.in_jail,
            "bankrupt": self.bankrupt,
            "turn_active": self.turn_active
        }

    @staticmethod
    def from_dict(data: Dict) -> "Player":
        """Khôi phục player từ dữ liệu JSON"""
        p = Player(data["id"], data["name"], data.get("money", 1500))
        p.position = data.get("position", 0)
        p.properties = data.get("properties", [])
        p.in_jail = data.get("in_jail", False)
        p.bankrupt = data.get("bankrupt", False)
        p.turn_active = data.get("turn_active", False)
        return p
    # ======================================
    # 🔍 Debug
    # ======================================

    def __repr__(self):
        return f"<Player {self.name}: ${self.money}, pos={self.position}, jail={self.in_jail}>"
