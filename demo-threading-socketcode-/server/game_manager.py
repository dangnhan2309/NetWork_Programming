 
import random
from player import Player
from board import Board

class GameManager:
    def __init__(self, players):
        self.players = players      # Danh sách người chơi
        self.board = Board()        # Bàn cờ
        self.current_turn = 0       # Người chơi hiện tại (theo index)

    def roll_dice(self):
        """Đổ xúc xắc 2 lần (2 viên)."""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return dice1 + dice2, (dice1 == dice2)  # Tổng, có double không

    def next_turn(self):
        """Chuyển lượt chơi sang người tiếp theo."""
        self.current_turn = (self.current_turn + 1) % len(self.players)

    def play_turn(self):
        """Xử lý 1 lượt đi của người chơi hiện tại."""
        player = self.players[self.current_turn]
        print(f"\n🔹 Turn: {player.name}")

        # 1. Đổ xúc xắc
        steps, is_double = self.roll_dice()
        print(f"{player.name} rolled {steps} (double={is_double})")

        # 2. Di chuyển
        player.move(steps)
        current_tile = self.board.get_tile(player.position)

        # 3. Xử lý ô đất / ô đặc biệt
        self.handle_tile(player, current_tile)

        # 4. Nếu không double → chuyển lượt
        if not is_double:
            self.next_turn()

    def handle_tile(self, player, tile):
        """Xử lý logic khi người chơi đứng ở 1 ô trên bàn cờ."""
        if tile["type"] == "property":
            if tile["owner"] is None:
                print(f"{tile['name']} is available for ${tile['price']}")
                # Tạm: auto mua nếu đủ tiền
                if player.money >= tile["price"]:
                    player.buy_property(tile["name"], tile["price"])
                    tile["owner"] = player
            elif tile["owner"] != player:
                rent = tile["rent"]
                player.pay_rent(tile["owner"], rent)
        elif tile["type"] == "tax":
            print(f"{player.name} pays tax ${tile['amount']}")
            player.pay_tax(tile["amount"])
        elif tile["type"] == "jail":
            print(f"{player.name} goes to jail!")
            player.jail_time()
        elif tile["type"] == "chance":
            print(f"{player.name} draws a lucky card")
            player.draw_lucky_card()
        else:
            print(f"{player.name} landed on {tile['name']}")
