<<<<<<< Updated upstream
 
=======
import asyncio
import random
from typing import Dict, Optional, Callable, List
from .player import Player
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
        self.has_rolled = False

    def set_broadcast_callback(self, callback: Callable):
        self.broadcast_callback = callback

    def add_player(self, name: str, websocket=None) -> bool:
        if len(self.players) >= MAX_PLAYERS:
            return False
        if name in self.players:
            return False
            
        player = Player(name)
        self.players[name] = player
        self.player_connections[name] = websocket
        self.player_order.append(name)
        
        print(f"🎮 Player joined: {name} (Total: {len(self.players)}/{MAX_PLAYERS})")
        
        # Hiển thị board khi có player
        self.display_game_state()
        
        # Tự động bắt đầu game khi đủ 2 player
        if len(self.players) >= 2 and self.game_state == GAME_WAITING:
            asyncio.create_task(self.start_game())
            
        return True

    def remove_player(self, name: str):
        if name in self.players:
            del self.players[name]
            if name in self.player_connections:
                del self.player_connections[name]
            if name in self.player_order:
                self.player_order.remove(name)
                
            print(f"🚪 Player left: {name}")
            
            if len(self.players) < 2:
                self.game_state = GAME_WAITING
                self.current_turn = 0
                print("⏳ Waiting for more players...")
            
            self.display_game_state()

    def roll_dice(self):
        return U.roll_dice()

    def next_turn(self):
        if not self.players:
            return
            
        self.current_turn = (self.current_turn + 1) % len(self.player_order)
        current_player = self.get_current_player()
        
        if current_player:
            print(f"\n🎲 Lượt của: {current_player.name}")
            asyncio.create_task(self.broadcast_state())

    async def start_game(self):
        print(f"\n🎯 Starting game in {GAME_START_DELAY} seconds...")
        await asyncio.sleep(GAME_START_DELAY)
        
        self.game_state = GAME_PLAYING
        self.current_turn = 0
        current_player = self.get_current_player()
        
        print(f"\n🎉 GAME STARTED!")
        print(f"👥 Players: {', '.join(self.player_order)}")
        print(f"🎲 First turn: {current_player.name}")
        
        # Broadcast game started message
        if self.broadcast_callback:
            await self.broadcast_callback({
                "type": "game_started",
                "message": "Game has started!",
                "first_player": current_player.name
            })
        
        self.display_game_state()
        await self.broadcast_state()  # Đảm bảo broadcast state

    def get_current_player(self) -> Optional[Player]:
        if not self.player_order or self.game_state != GAME_PLAYING:
            return None
        current_name = self.player_order[self.current_turn]
        return self.players.get(current_name)

    def handle_player_action(self, player_name: str, action: str, data: dict = None) -> dict:
        player = self.players.get(player_name)
        if not player:
            return {C.K_TYPE: C.ERROR, C.K_MSG: "Player not found"}
            
        current = self.get_current_player()
        if not current or current.name != player_name:
            return {C.K_TYPE: C.ERROR, C.K_MSG: "Not your turn"}

        if action == "ROLL":
            return self.handle_roll(player_name)
        elif action == "BUY":
            return self.handle_buy(player_name)
        elif action == "END_TURN":
            self.next_turn()
            result = {C.K_TYPE: C.INFO, C.K_MSG: f"{player_name} ended turn"}
            self.display_game_state()
            return result
        else:
            return {C.K_TYPE: C.ERROR, C.K_MSG: "Unknown action"}

    def handle_end_turn(self, player_name: str):
        current_player = self.get_current_player()
        if not current_player or current_player.name != player_name:
            return {
                C.K_TYPE: C.ERR,
                C.K_MSG: "❌ Không phải lượt của bạn!"
            }

        # Chuyển lượt
        self.current_turn = (self.current_turn + 1) % len(self.player_order)
        self.has_rolled = False
        next_player = self.get_current_player()

        print(f"🔄 {player_name} đã kết thúc lượt. Đến lượt {next_player.name}")

        return {
            C.K_TYPE: C.INFO,
            C.K_MSG: f"🔄 {player_name} đã kết thúc lượt. Đến lượt {next_player.name}"
        }



    def handle_roll(self, player_name: str):
        current_player = self.get_current_player()
        if not current_player or current_player.name != player_name:
            return {
                C.K_TYPE: C.ERR,
                C.K_MSG: "❌ Không phải lượt của bạn!"
            }

        if self.has_rolled:
            return {
                C.K_TYPE: C.ERR,
                C.K_MSG: "❌ Bạn đã roll trong lượt này rồi!"
            }

        player = self.players[player_name]
        dice = self.roll_dice()
        steps = dice["total"]

        old_position = player.position
        player.move(steps)
        tile = self.board.get_tile(player.position)

        print(f"🎲 {player_name} rolled {dice['dice']} = {steps}")
        print(f"📍 Moved from {old_position} to {player.position}: {tile['name']}")

        result = self.handle_tile(player, tile)

        self.display_game_state()
        asyncio.create_task(self.broadcast_state())

        self.has_rolled = True  # đánh dấu đã roll

        return {
            C.K_TYPE: C.INFO,
            C.K_MSG: f"{player_name} rolled {steps}",
            "dice": dice,
            "tile": tile,
            "result": result
        }



    def handle_buy(self, player_name: str):
        player = self.players[player_name]
        tile = self.board.get_tile(player.position)
        
        if tile.get("owner") is not None:
            return {C.K_TYPE: C.ERROR, C.K_MSG: "Property already owned"}
            
        if tile.get("type") not in ["property", "railroad", "utility"]:
            return {C.K_TYPE: C.ERROR, C.K_MSG: "Cannot buy this tile type"}
            
        if player.money < tile["price"]:
            return {C.K_TYPE: C.ERROR, C.K_MSG: "Not enough money"}
            
        # Thực hiện mua
        player.buy_property(tile["name"], tile["price"])
        tile["owner"] = player
        
        print(f"💰 {player_name} bought {tile['name']} for ${tile['price']}")
        
        self.display_game_state()
        asyncio.create_task(self.broadcast_state())
        
        return {
            C.K_TYPE: C.INFO, 
            C.K_MSG: f"{player_name} bought {tile['name']} for ${tile['price']}"
        }

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
                    "money": p.money, 
                    "position": p.position,
                    "properties": list(p.properties.keys())
                }
                for p in self.players.values()
            ]
        }

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
            print(f"     💰 ${player.money} | 📍 Vị trí: {player.position}")
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
