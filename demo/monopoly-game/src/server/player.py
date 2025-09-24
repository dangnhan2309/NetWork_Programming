import random


class Player:
    def __init__(self, name="", position="A1", money=1500):
        self.name = name
        self.position = position
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
        self.position = (self.position + steps) % 40

        # Nếu vị trí mới nhỏ hơn vị trí cũ, người chơi đã đi qua ô GO.
        # Ví dụ: từ ô 38 di chuyển 5 bước, vị trí mới là 3 (43 % 40).
        if self.position < old_position:
            self.money += 200
            print(f"{self.name} đã đi qua ô GO và nhận được 200 đô la.")

        print(f"{self.name} di chuyển {steps} bước. Vị trí mới là {self.position}.")

    def buy_property(self, property_name, cost):
            """
            Mua tài sản trên ô hiện tại.
            Args:
                property_name (str): Tên của tài sản.
                cost (int): Chi phí để mua tài sản.
            """
            if self.money >= cost:
                self.money -= cost
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
        self.position = 10  # Ô J11 (Go to Jail)
        self.in_jail = True
        self.jail_turns = 3  # Số lượt ở tù
        print(f"{self.name} đã bị đưa vào tù.")

    def build_house(self, property_name):
        """Nâng cấp tài sản (xây khách sạn)."""
        if property_name in self.properties and self.properties[property_name]['houses'] == 4:
            self.properties[property_name]['houses'] = 5  # 5 houses = 1 hotel
            print(f"{self.name} đã xây một khách sạn trên {property_name}.")
        else:
            print(f"Không thể nâng cấp {property_name} thành khách sạn.")

    def upgrade_property(self, property_name):
        """Nâng cấp tài sản (xây khách sạn)."""
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
    # ----- Helper methods -----
    def __str__(self):
        return f"{self.name} at {self.position} with ${self.money}"
