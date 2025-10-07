"""
Player class
"""

class Player:
    def __init__(self, player_id: str, name: str, websocket):
        self.id = player_id
        self.name = name
        self.websocket = websocket
        self.money = 1500
        self.position = 0
        self.properties = {}
        self.in_jail = False
        self.jail_turns = 0
        self.is_bankrupt = False

    def move(self, steps: int):
        """Di chuyển player"""
        self.position = (self.position + steps) % 40
        return self.position

    def buy_property(self, property_name: str, price: int):
        """Mua property"""
        if self.money >= price:
            self.money -= price
            self.properties[property_name] = {
                "price": price,
                "mortgaged": False
            }
            return True
        return False

    def pay_rent(self, owner, amount: int):
        """Trả tiền thuê"""
        if self.money >= amount:
            self.money -= amount
            owner.money += amount
            return True
        else:
            self.is_bankrupt = True
            return False

    def to_dict(self):
        """Chuyển thành dictionary để gửi client"""
        return {
            "id": self.id,
            "name": self.name,
            "money": self.money,
            "position": self.position,
            "properties": list(self.properties.keys()),
            "isBankrupt": self.is_bankrupt
        }