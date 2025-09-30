import random
from ..shared.board import Board
from .player import Player
<<<<<<< Updated upstream
from .Game_tracking import Tracker

class GameManager:
    def __init__(self, players=None):
        self.board = Board()        # Bàn cờ
        self.room = 0 #->late update
        self.Tracker = Tracker()
=======
from .board import Board
from src.shared import constants as C
from src.shared import utils as U


MAX_PLAYERS = 4
GAME_WAITING = "WAITING"
GAME_PLAYING = "PLAYING"
GAME_ENDED = "ENDED"
GAME_START_DELAY = 2.0

class GameManager:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.player_connections: Dict[str, any] = {}
        self.board = Board()
        self.current_turn = 0
        self.game_state = GAME_WAITING
        self.broadcast_callback: Optional[Callable] = None
        self.player_order: List[str] = []
        self.material ={"Chance deck" : C.community_chest_cards[:],"Community deck" : C.chance_cards[:]}
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
=======
    def handle_roll(self, player_name: str):
        player = self.players[player_name]
        dice = self.roll_dice()
        steps = dice["total"]
        
        old_position = player.position
        player.move(steps)
        tile = self.board.get_tile(player.position)
        
        print(f"🎲 {player_name} rolled {dice['dice']} = {steps}")
        print(f"📍 Moved from {old_position} to {player.position}: {tile['name']}")
        if tile["type"] in ["chance", "community_chest"]:
            if tile["type"] == "chance":
                card = C.draw_card(self.material["Chance deck"],False)
                print(card)
            else:  # community_chest
                card = C.draw_card(self.material["Community deck"],False)
                print(card)

            result = self.handler_card_content(player, card)
        else:
            result = self.handle_tile(player, tile)

        self.display_game_state()
        asyncio.create_task(self.broadcast_state())
        
        return {
            C.K_TYPE: C.INFO,
            C.K_MSG: f"{player_name} rolled {steps}",
            "dice": dice,
            "tile": tile,
            "result": result
        }
>>>>>>> Stashed changes

#-----------------Room----------

<<<<<<< Updated upstream

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
=======
    def handle_tile(self, player: Player, tile: dict):
        tile_type = tile["type"]
        
        if tile_type == "property" and tile.get("owner") and tile["owner"] != player:
            rent = tile.get("rent", 0)
            result = player.pay_rent(tile["owner"], rent)
            return {
                "action": "paid_rent", 
                "amount": rent, 
                "to": tile["owner"].name,
                "success": result
            }
            
        elif tile_type == "tax":
            amount = tile.get("amount", 0)
            player.pay_tax(amount)
            return {"action": "paid_tax", "amount": amount}
            
        elif tile_type == "go":
            return {"action": "passed_go", "amount": 200}


        return {"action": "landed", "tile": tile["name"]}

    def handler_card_content(self, player: Player, card: str):
        """
        Xử lý nội dung lá bài được rút ra.
        Trả về dict action + thông tin chi tiết để log/game engine xử lý.
        """

        # Advance to Go
        if card.startswith("Advance to Go"):
            player.position = 0
            player.balance  += 200
            return {"action": "move", "to": 0, "amount": 200}

        # Bank error in your favor
        elif card.startswith("Bank error in your favor"):
            player.balance  += 200
            return {"action": "balance ", "amount": 200}

        # Doctor’s fees
        elif card.startswith("Doctor’s fees"):
            player.balance  -= 50
            return {"action": "balance ", "amount": -50}

        # Get out of Jail Free
        elif card.startswith("Get Out of Jail Free"):
            player.has_get_out_of_jail_card += 1
            return {"action": "jail_free"}

        # Go to Jail
        elif "Go to Jail" in card:
            player.position = "jail"
            player.in_jail = True
            return {"action": "jail"}

        # Go Back 3 Spaces
        elif card.startswith("Go Back 3 Spaces"):
            player.position -= 3
            return {"action": "move_back", "steps": 3}

        # Pay poor tax
        elif card.startswith("Pay poor tax"):
            player.balance -= 15
            return {"action": "balance ", "amount": -15}

        # Birthday / Opera Night → collect from others
        elif card.startswith("It is your birthday"):
            return {"action": "collect_from_others", "amount": 10}

        elif card.startswith("Grand Opera Night"):
            return {"action": "collect_from_others", "amount": 50}

        # Property repairs
        elif card.startswith("You are assessed for street repairs"):
            return {"action": "repairs", "house": 40, "hotel": 115}

        elif card.startswith("Make general repairs on all your property"):
            return {"action": "repairs", "house": 25, "hotel": 100}

        # Movement to named places
        elif card.startswith("Advance to Illinois Ave."):
            return {"action": "move", "to": "Illinois Ave"}

        elif card.startswith("Advance to St. Charles Place"):
            return {"action": "move", "to": "St. Charles Place"}

        elif card.startswith("Take a trip to Reading Railroad"):
            return {"action": "move", "to": "Reading Railroad"}

        elif card.startswith("Take a walk on the Boardwalk"):
            return {"action": "move", "to": "Boardwalk"}

        elif card.startswith("Advance token to nearest Utility"):
            return {"action": "nearest", "target": "utility"}

        elif card.startswith("Advance token to nearest Railroad"):
            return {"action": "nearest", "target": "railroad"}

        # Generic balance  events
        elif "Collect" in card:
            import re
            m = re.search(r"Collect \$([0-9]+)", card)
            if m:
                amount = int(m.group(1))
                player.balance += amount
                return {"action": "balance ", "amount": amount}

        elif "Pay" in card:
            import re
            m = re.search(r"Pay \$([0-9]+)", card)
            if m:
                amount = int(m.group(1))
                player.balance -= amount
                return {"action": "balance ", "amount": -amount}

        # fallback
        return {"action": "none", "card": card}

    async def broadcast_state(self):
        if self.broadcast_callback:
            state = self.get_game_state()
            await self.broadcast_callback(state)

    def get_game_state(self):
        return {
            "state": self.game_state,
            "current_turn": self.current_turn,
            "players": [
                {
                    "name": p.name, 
                    "balance ": p.balance ,
                    "position": p.position,
                    "properties": list(p.properties.keys())
>>>>>>> Stashed changes
                }
                for p in self.players
            ],

<<<<<<< Updated upstream
        }
        return {"action": "STATE", "data": state}
=======
    def display_game_state(self):
        """Hiển thị trạng thái game trên server console"""
        print("\n" + "="*60)
        print("🎯 MONOPOLY SERVER - GAME STATE")
        print("="*60)
        
        # Hiển thị board
        player_positions = {name: player.position for name, player in self.players.items()}
        self.board.render_board(player_positions)
        
        # Hiển thị thông tin players
        print(f"\n📊 PLAYERS ({len(self.players)}/{MAX_PLAYERS}):")
        for i, (name, player) in enumerate(self.players.items()):
            turn_indicator = " 🎲" if i == self.current_turn and self.game_state == GAME_PLAYING else ""
            print(f"  {i+1}. {name}{turn_indicator}")
            print(f"     💰 ${player.balance } | 📍 Vị trí: {player.position}")
            if player.properties:
                print(f"     🏠 Properties: {', '.join(player.properties.keys())}")
            print()
        
        # Hiển thị game state
        if self.game_state == GAME_WAITING:
            print("⏳ Game State: WAITING FOR PLAYERS...")
            needed = 2 - len(self.players)
            if needed > 0:
                print(f"   Need {needed} more player(s) to start")
        elif self.game_state == GAME_PLAYING:
            current_player = self.get_current_player()
            if current_player:
                print(f"🎲 CURRENT TURN: {current_player.name}")
                current_tile = self.board.get_tile(current_player.position)
                print(f"📍 Current tile: {current_tile['name']} ({current_tile['type']})")
        
        print("="*60)
>>>>>>> Stashed changes
