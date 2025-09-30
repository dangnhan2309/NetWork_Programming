import random
from typing import Any

# Thử lấy map tên ô -> index nếu có (không có cũng không sao)
try:
    from .tiles import TILES  # danh sách tên 40 ô nếu có
    NAME_TO_INDEX = {name: i for i, name in enumerate(TILES)} if isinstance(TILES, (list, tuple)) else {}
except Exception:
    TILES = []
    NAME_TO_INDEX = {}


def _to_index(pos: Any) -> int:
    """
    Chuẩn hoá vị trí về index 0..39.
    - int: dùng luôn (mod 40)
    - str số ('10'): đổi sang int
    - str tên ('A1'...) nếu có NAME_TO_INDEX thì tra cứu, không có thì về 0
    """
    try:
        if isinstance(pos, int):
            return pos % 40
        if isinstance(pos, str):
            if pos.isdigit():
                return int(pos) % 40
            return int(NAME_TO_INDEX.get(pos, 0)) % 40
    except Exception:
        pass
    return 0


class Player:
    def __init__(self, name: str = "", position: Any = "A1", money: int = 1500):
        self.name = name
        # 🔧 Luôn lưu vị trí dạng INT 0..39 (nhưng nhận string/số đều OK)
        self.position = _to_index(position)

        self.money = money
        self.properties = {}
        self.in_jail = False
        self.jail_turns = 0
        self.is_bankrupt = False

    # Cho code khác đọc chỉ số ô theo chuẩn (tương thích với renderer)
    @property
    def position_index(self) -> int:
        return int(self.position)

    # ----- Game actions -----

    @staticmethod
    def roll_dice():
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1 + dice2

    def move(self, steps: int):
        """
        Cập nhật vị trí trên bàn cờ.
        Xử lý đi qua ô GO (+200$).
        """
        steps = int(steps)
        old_position = int(self.position)
        self.position = (old_position + steps) % 40

        if self.position < old_position:
            self.money += 200
            print(f"{self.name} đã đi qua ô GO và nhận được 200 đô la.")

        print(f"{self.name} di chuyển {steps} bước. Vị trí mới là {self.position}.")

    def buy_property(self, property_name, cost):
        if self.money >= cost:
            self.money -= cost
            self.properties[property_name] = {'cost': cost, 'houses': 0}
            print(f"{self.name} đã mua {property_name} với giá {cost}$.")
        else:
            print(f"{self.name} không đủ tiền để mua {property_name}.")

    def sell_property(self, property_name, price):
        if property_name in self.properties:
            self.money += price
            del self.properties[property_name]
            print(f"{self.name} đã bán {property_name} với giá {price}$.")
        else:
            print(f"{self.name} không sở hữu {property_name}.")

    def pay_rent(self, owner, amount):
        if self.money >= amount:
            self.money -= amount
            owner.money += amount
            print(f"{self.name} đã trả {amount}$ tiền thuê cho {owner.name}.")
        else:
            print(f"{self.name} không đủ tiền để trả tiền thuê. Bắt đầu quá trình phá sản.")
            self.try_to_avoid_bankruptcy(amount)
            if self.money < amount:
                print(f"{self.name} đã phá sản! Tất cả tài sản được chuyển cho {owner.name}.")
                for prop in list(self.properties.keys()):
                    if self.properties[prop]['houses'] > 0:
                        self.money += self.properties[prop]['houses'] * (50 / 2)
                    owner.properties[prop] = self.properties[prop]
                    del self.properties[prop]
                owner.money += self.money
                self.money = 0
                self.is_bankrupt = True

    def pay_tax(self, amount):
        if self.money >= amount:
            self.money -= amount
            print(f"{self.name} đã trả {amount}$ tiền thuế.")
        else:
            print(f"Không đủ tiền để trả {amount}$ thuế.")

    def draw_lucky_card(self):
        from random import choice
        lucky_cards = ["Nhận 50$", "Mất 25$", "Đi thẳng vào tù"]
        card_effect = choice(lucky_cards)
        print(f"{self.name} rút một lá bài may mắn: '{card_effect}'.")
        if "Nhận" in card_effect:
            self.money += 50
        elif "Mất" in card_effect:
            self.money -= 25
        elif "tù" in card_effect:
            self.jail_time()

    def jail_time(self):
        self.position = 10  # Jail
        self.in_jail = True
        self.jail_turns = 3
        print(f"{self.name} đã bị đưa vào tù.")

    def build_house(self, property_name):
        if property_name in self.properties and self.properties[property_name]['houses'] == 4:
            self.properties[property_name]['houses'] = 5
            print(f"{self.name} đã xây một khách sạn trên {property_name}.")
        else:
            print(f"Không thể nâng cấp {property_name} thành khách sạn.")

    def upgrade_property(self, property_name):
        if property_name in self.properties and self.properties[property_name]['houses'] == 4:
            self.properties[property_name]['houses'] = 5
            print(f"{self.name} đã xây một khách sạn trên {property_name}.")
        else:
            print(f"Không thể nâng cấp {property_name} thành khách sạn.")

    def transaction(self, other_player, amount):
        if self.money >= amount:
            self.money -= amount
            other_player.money += amount
            print(f"{self.name} đã chuyển {amount}$ cho {other_player.name}.")
        else:
            print(f"{self.name} không đủ tiền để thực hiện giao dịch.")

    def try_to_avoid_bankruptcy(self, debt_amount):
        while self.money < debt_amount and self.properties:
            property_to_mortgage = list(self.properties.keys())[0]
            mortgage_value = self.properties[property_to_mortgage]['cost'] / 2
            self.money += mortgage_value
            print(f"{self.name} đã cầm cố {property_to_mortgage} để có thêm {mortgage_value}$.")
            del self.properties[property_to_mortgage]

    def __str__(self):
        return f"{self.name} at {self.position} with ${self.money}"
