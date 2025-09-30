from typing import Dict

class Player:
    def __init__(self, name: str):
        self.name = name
        self.money = 1500
        self.position = 0
        self.properties: Dict[str, dict] = {}
        self.is_bankrupt = False
        self.jail_turns = 0
        self.has_get_out_of_jail_card = False

    def move(self, steps: int):
        old_pos = self.position
        self.position = (self.position + steps) % 40
        
        # Nhận $200 khi đi qua GO
        if old_pos + steps >= 40:
            self.money += 200
            print(f"💰 {self.name} passed GO and collected $200")

    def buy_property(self, property_name: str, price: int):
        """Mua tài sản"""
        if self.money >= price:
            self.money -= price
            self.properties[property_name] = {
                "name": property_name,
                "price": price,
                "houses": 0,
                "hotel": False,
                "mortgaged": False
            }
            return True
        return False

    def pay_rent(self, owner, amount: int) -> bool:
        """Trả tiền thuê, trả về True nếu thành công, False nếu phá sản"""
        if self.money >= amount:
            self.money -= amount
            owner.money += amount
            print(f"💸 {self.name} paid ${amount} rent to {owner.name}")
            return True
        else:
            # Phá sản
            self.is_bankrupt = True
            owner.money += self.money
            self.money = 0
            print(f"💀 {self.name} went bankrupt! Properties transferred to {owner.name}")
            
            # Chuyển tất cả tài sản
            for prop_name, prop in self.properties.items():
                owner.properties[prop_name] = prop
            self.properties.clear()
            
            return False

    def pay_tax(self, amount: int):
        """Trả thuế"""
        if self.money >= amount:
            self.money -= amount
            print(f"🏛️ {self.name} paid ${amount} tax")
        else:
            self.is_bankrupt = True
            self.money = 0
            print(f"💀 {self.name} went bankrupt from tax!")

    def go_to_jail(self):
        """Đi vào tù"""
        self.position = 10  # Vị trí Jail
        self.jail_turns = 3
        print(f"🔒 {self.name} went to jail!")

    def get_out_of_jail(self):
        """Ra tù"""
        if self.jail_turns > 0:
            self.jail_turns = 0
            print(f"🔓 {self.name} got out of jail!")

    def add_money(self, amount: int):
        """Thêm tiền"""
        self.money += amount
        print(f"💰 {self.name} received ${amount}")

    def __str__(self):
        return f"Player({self.name}, ${self.money}, pos:{self.position})"

    def __repr__(self):
        return self.__str__()