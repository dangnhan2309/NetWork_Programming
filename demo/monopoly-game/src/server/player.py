import random

# ----- Constants -----
BOARD_SIZE = 40
GO_BONUS = 200
JAIL_POSITION = 10


class Player:
    def __init__(self, name="", position=0, money=1500):
        self.name = name
        # position should be an int in [0, 39]
        self.position = int(position) if isinstance(position, int) or str(position).isdigit() else 0
        self.money = money
        self.properties = {}
        self.in_jail =False
        self.jail_turns = 0
        self.is_bankrupt = False

    # ----- Game actions -----

    @staticmethod
    def roll_dice():
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1 + dice2

    def move(self, steps):
        """
        Cập nhật vị trí của người chơi trên bàn cờ.
        Xử lý việc đi qua ô GO và nhận tiền.
        """
        # Lưu lại vị trí cũ để kiểm tra xem người chơi có đi qua ô GO không
        old_position = self.position

        # Cập nhật vị trí mới bằng cách cộng thêm số bước.
        self.position = (self.position + steps) % BOARD_SIZE

        # Nếu vị trí mới nhỏ hơn vị trí cũ, người chơi đã đi qua ô GO.
        # Ví dụ: từ ô 38 di chuyển 5 bước, vị trí mới là 3 (43 % 40).
        if self.position < old_position:
            self.money += GO_BONUS
            print(f"{self.name} đã đi qua ô GO và nhận được {GO_BONUS} đô la.")

        print(f"{self.name} di chuyển {steps} bước. Vị trí mới là {self.position}.")

    def can_buy_property(self, cost: int) -> bool:
        return self.money >= cost and not self.is_bankrupt and not self.in_jail

    def buy_property(self, property_name, cost):
        """
        Mua tài sản trên ô hiện tại.
        Args:
            property_name (str): Tên của tài sản.
            cost (int): Chi phí để mua tài sản.
        """
        if self.can_buy_property(cost):
            self.money -= cost
            # default: 0 houses; 5 means hotel
            self.properties[property_name] = {'cost': cost, 'houses': 0}
            print(f"{self.name} đã mua {property_name} với giá {cost}$.")
        else:
            print(f"{self.name} không đủ tiền để mua {property_name}.")

    def sell_property(self, property_name, price):
        """Bán tài sản đang sở hữu."""
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
            # Xử lý phá sản
            print(f"{self.name} không đủ tiền để trả tiền thuê. Bắt đầu quá trình phá sản.")
            # Logic cầm cố và bán tài sản để cố gắng trả nợ
            self.try_to_avoid_bankruptcy(amount)

            # Nếu vẫn không đủ tiền sau khi đã cố gắng
            if self.money < amount:
                print(f"{self.name} đã phá sản! Tất cả tài sản được chuyển cho {owner.name}.")
                # Chuyển tất cả tài sản cho chủ nợ
                for prop in list(self.properties.keys()):
                    # Nếu có nhà/khách sạn, bán lại cho ngân hàng trước
                    if self.properties[prop]['houses'] > 0:
                        # Giả định giá bán = 1/2 giá xây dựng
                        self.money += self.properties[prop]['houses'] * (50 / 2)  # Ví dụ

                    # Chuyển tài sản cho chủ nợ
                    owner.properties[prop] = self.properties[prop]
                    del self.properties[prop]

                # Chuyển số tiền còn lại cho chủ nợ
                owner.money += self.money
                self.money = 0

                # Đánh dấu người chơi này đã thua cuộc
                self.is_bankrupt = True

    def pay_tax(self, amount):
        """Trả thuế."""
        if self.money >= amount:
            self.money -= amount
            print(f"{self.name} đã trả {amount}$ tiền thuế.")
        else:
            print(f"Không đủ tiền để trả {amount}$ thuế.")
    def draw_lucky_card(self):
        """Rút thẻ may mắn (random event)."""
        # Đây là một phương thức giả định. Trong thực tế, bạn sẽ cần một danh sách
        # các lá bài và chọn ngẫu nhiên.
        from random import choice
        lucky_cards = ["Nhận 50$", "Mất 25$", "Đi thẳng vào tù"]
        card_effect = choice(lucky_cards)
        print(f"{self.name} rút một lá bài may mắn: '{card_effect}'.")
        # Thêm logic để xử lý các hiệu ứng của lá bài
        if "Nhận" in card_effect:
            self.money += 50
        elif "Mất" in card_effect:
            self.money -= 25
        elif "tù" in card_effect:
            self.jail_time()
    def jail_time(self):
        """Xử lý khi bị vào tù."""
        self.position = JAIL_POSITION
        self.in_jail = True
        self.jail_turns = 3  # Số lượt ở tù
        print(f"{self.name} đã bị đưa vào tù.")

    def release_from_jail(self):
        if not self.in_jail:
            return
        self.in_jail = False
        self.jail_turns = 0
        print(f"{self.name} đã được thả khỏi tù.")

    def add_house(self, property_name: str):
        """Xây thêm 1 nhà (0 -> 1 -> 2 -> 3 -> 4). Khi đạt 4 thì lần sau sẽ thành hotel (5)."""
        if property_name not in self.properties:
            print(f"{self.name} không sở hữu {property_name}.")
            return
        houses = self.properties[property_name]['houses']
        if 0 <= houses < 4:
            self.properties[property_name]['houses'] = houses + 1
            print(f"{self.name} đã xây thêm 1 nhà trên {property_name} (tổng {houses + 1}).")
        else:
            print(f"{property_name} đã có đủ nhà để nâng cấp lên khách sạn.")

    def upgrade_property(self, property_name: str):
        """Nâng cấp tài sản lên khách sạn (yêu cầu 4 nhà)."""
        if property_name in self.properties and self.properties[property_name]['houses'] == 4:
            self.properties[property_name]['houses'] = 5  # 5 houses = 1 hotel
            print(f"{self.name} đã xây một khách sạn trên {property_name}.")
        else:
            print(f"Không thể nâng cấp {property_name} thành khách sạn.")

    def transaction(self, other_player, amount):
        """Chuyển tiền giữa 2 người chơi."""
        if self.money >= amount:
            self.money -= amount
            other_player.money += amount
            print(f"{self.name} đã chuyển {amount}$ cho {other_player.name}.")
        else:
            print(f"{self.name} không đủ tiền để thực hiện giao dịch.")

    def try_to_avoid_bankruptcy(self, debt_amount):
        """
        Giả định một phương thức để người chơi cố gắng huy động tiền.
        Thực tế, bạn sẽ cần một vòng lặp để người chơi quyết định bán gì.
        """
        while self.money < debt_amount and self.properties:
            # Giả định người chơi tự động bán/cầm cố tài sản
            property_to_mortgage = list(self.properties.keys())[0]
            # Giả định cầm cố được 50% giá trị ban đầu
            mortgage_value = self.properties[property_to_mortgage]['cost'] / 2
            self.money += mortgage_value
            print(f"{self.name} đã cầm cố {property_to_mortgage} để có thêm {mortgage_value}$.")
            del self.properties[property_to_mortgage]
        if self.money < debt_amount and not self.properties:
            self.is_bankrupt = True
            print(f"{self.name} không thể trả nợ và đã phá sản.")
    # ----- Helper methods -----
    def __str__(self):
        return f"{self.name} at {self.position} with ${self.money}"

    def release_from_jail(self):
        pass
def _calculate_property_worth(prop: dict) -> int:
    base = int(prop.get('cost', 0))
    houses = int(prop.get('houses', 0))
    # Example heuristic: each house adds 50
    return base + (50 * max(0, houses if houses <= 4 else 5))

def get_net_worth(player: Player) -> int:
    total = player.money
    for p in player.properties.values():
        total += _calculate_property_worth(p)
    return total