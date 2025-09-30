import random
from ..shared.board import Board
from .player import Player
from .Game_tracking import Tracker

class GameManager:
    def __init__(self, players=None):
        self.board = Board()        # Bàn cờ
        self.room = 0 #->late update
        self.Tracker = Tracker()

    # ---- Player Management ----
    #----player in/out ---
    def recieve_player_input(self,request):
        pass

    def send_response(self,response):
        pass
    def start_game(self):
        print("Game Start")
        while not self.Tracker.is_game_over():
            self.game_handler()

    def game_handler(self):
        current_player = self.Tracker.get_current_player()
        print(f"Turn of {current_player.name}")
        # wait for user_action
        self.Tracker.next_turn()

    def create_room(self):
        pass
    def add_player(self, name: str,) -> bool:
        new_players = Player(name)
        if self.checkroom :
            self.Tracker.add_player(new_players)
            return True
        else:
            return False
    def checkroom(self,id_room):
        pass
    def remove_players(self,player: Player):
        try:
            # anoy that will remove players
            print(f"Admin is removing players.....")
            # return all the assets first =

            # board -> remove name  in the board
            # game_material -> return assets
            # anoun
            # players -> remove players
            self.players.remove(player)

        except Exception as e:
            print(e)

        return
    def remove_bankrupt_players(self):
        self.players = [p for p in self.players if not p.is_bankrupt]
        if self.current_turn >= len(self.players):
            self.current_turn = 0 if self.players else 0

    def is_game_over(self) -> bool:
        return len([p for p in self.players if not p.is_bankrupt]) <= 1
#------------------ game function ------------------

    def announce_winner(self) -> str:
        alive = [p for p in self.players if not p.is_bankrupt]
        return alive[0].name if len(alive) == 1 else ""

    def roll_dice(self, player_name: str | None = None):
        """Đổ xúc xắc 2 lần (2 viên). Nếu cung cấp player_name sẽ áp dụng lượt đi cho người đó."""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        is_double = (dice1 == dice2)

        moved_player = None
        if player_name:
            moved_player = next((p for p in self.players if p.name == player_name), None)
        if moved_player is None and self.players:
            moved_player = self.players[self.current_turn]

        if moved_player:
            if moved_player.in_jail:
                moved_player.jail_turns -= 1
                if moved_player.jail_turns <= 0:
                    moved_player.release_from_jail()
            else:
                moved_player.move(total)
                current_tile = self.board.get_tile(moved_player.position)
                self.handle_tile(moved_player, current_tile)

            name = moved_player.name
            if is_double:
                self._double_streak[name] = self._double_streak.get(name, 0) + 1
                if self._double_streak[name] >= 3:
                    moved_player.jail_time()
                    self._double_streak[name] = 0
                    self.next_turn()
            else:
                self._double_streak[name] = 0
                self.next_turn()

        return {
            "player": moved_player.name if moved_player else None,
            "dice": [dice1, dice2],
            "total": total,
            "double": is_double,
            "pos": moved_player.position if moved_player else None,
            "money": moved_player.money if moved_player else None,
        }

    def next_turn(self):
        """Chuyển lượt chơi sang người tiếp theo, bỏ qua bankrupt."""
        if not self.players:
            return
        start = self.current_turn
        while True:
            self.current_turn = (self.current_turn + 1) % len(self.players)
            if not self.players[self.current_turn].is_bankrupt:
                break
            if self.current_turn == start:
                break
    def play_turn(self):
        """Xử lý 1 lượt đi của người chơi hiện tại."""
        player = self.players[self.current_turn]
        print(f"\n🔹 Turn: {player.name}")

        result = self.roll_dice(player.name)
        print(f"{player.name} rolled {result['total']} (double={result['double']})")

        current_tile = self.board.get_tile(player.position)

        self.handle_tile(player, current_tile)
        # next_turn handled in roll_dice

    def handle_tile(self, player, tile):
        """Xử lý logic khi người chơi đứng ở 1 ô trên bàn cờ."""
        if tile["type"] == "property":
            if tile["owner"] is None:
                print(f"{tile['name']} is available for ${tile['price']}")
                # Bot: auto mua nếu đủ tiền
                if player.can_buy_property(tile["price"]):
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


#-----------------Room----------


    # ---- State Packet ----
    def make_state_packet(self) -> dict:
        state = {
            "players": [
                {
                    "name": p.name,
                    "money": p.money,
                    "pos": p.position,
                    "in_jail": p.in_jail,
                    "bankrupt": p.is_bankrupt,
                }
                for p in self.players
            ],

        }
        return {"action": "STATE", "data": state}
