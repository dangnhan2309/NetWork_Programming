"""
Game Room với State Machine
"""

import asyncio
import random
import json
from typing import Dict, List, Optional
from .board import Board
from .player import Player
from ..shared.constants import *

class GameRoom:
    def __init__(self, room_id: str, room_name: str = "Phòng chơi"):
        self.room_id = room_id
        self.room_name = room_name
        self.players: Dict[str, Player] = {}
        self.board = Board()
        self.state = STATE_EMPTY
        self.current_turn_index = 0
        self.has_rolled = False
        self.winner = None
        
        # BỎ PRINT Ở ĐÂY - để RoomManager in thôi
        # print(f"🏠 Room created: {room_id} - '{room_name}'")

    def add_player(self, player_id: str, player_name: str, websocket) -> bool:
        """Thêm player vào room"""
        if len(self.players) >= MAX_PLAYERS:
            return False
            
        player = Player(player_id, player_name, websocket)
        self.players[player_id] = player
        
        # Update state
        if self.state == STATE_EMPTY:
            self.state = STATE_WAITING
            
        print(f"🎮 {player_name} joined room {self.room_id}. Players: {len(self.players)}/{MAX_PLAYERS}")
        return True

    def remove_player(self, player_id: str):
        """Xóa player khỏi room"""
        if player_id in self.players:
            player_name = self.players[player_id].name
            del self.players[player_id]
            
            print(f"🚪 {player_name} left room {self.room_id}. Players: {len(self.players)}/{MAX_PLAYERS}")
            
            # Update state
            if len(self.players) == 0:
                self.state = STATE_EMPTY
                print(f"🏠 Room {self.room_id} is now empty")
            elif self.state == STATE_PLAYING and len(self.players) < MIN_PLAYERS:
                self.state = STATE_WAITING
                self.current_turn_index = 0
                print(f"⏸️ Game paused in room {self.room_id} - waiting for more players")

    def can_start_game(self) -> bool:
        """Kiểm tra có thể bắt đầu game không"""
        return len(self.players) >= MIN_PLAYERS and self.state == STATE_WAITING

    async def start_game(self):
        """Bắt đầu game"""
        if self.can_start_game():
            self.state = STATE_PLAYING
            self.current_turn_index = 0
            self.has_rolled = False
            self.winner = None
            
            print(f"🎉 Game started in room {self.room_id} with {len(self.players)} players")
            
            # Broadcast game started
            await self.broadcast({
                "type": TYPE_INFO,
                "event": "gameStarted",
                "message": "🎮 Game started!",
                "board": self.get_board_state(),
                "currentTurn": self.get_current_player().id
            })

    def get_current_player(self) -> Optional[Player]:
        """Lấy player hiện tại đến lượt"""
        if not self.players or self.state != STATE_PLAYING:
            return None
            
        player_ids = list(self.players.keys())
        if not player_ids:
            return None
            
        current_id = player_ids[self.current_turn_index % len(player_ids)]
        return self.players.get(current_id)

    def next_turn(self):
        """Chuyển lượt"""
        if not self.players or self.state != STATE_PLAYING:
            return
            
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        self.has_rolled = False
        
        current_player = self.get_current_player()
        if current_player:
            print(f"🎲 Turn changed to: {current_player.name} in room {self.room_id}")

    def roll_dice(self) -> dict:
        """Tung xúc xắc"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        return {
            "dice": [dice1, dice2],
            "total": dice1 + dice2,
            "is_double": dice1 == dice2
        }

    async def handle_roll_dice(self, player_id: str) -> dict:
        """Xử lý tung xúc xắc"""
        current_player = self.get_current_player()
        if not current_player or current_player.id != player_id:
            return {"type": TYPE_ERROR, "message": "❌ Not your turn!"}

        if self.has_rolled:
            return {"type": TYPE_ERROR, "message": "❌ Already rolled this turn!"}

        # Roll dice
        dice_result = self.roll_dice()
        steps = dice_result["total"]
        
        # Move player
        old_position = current_player.position
        new_position = current_player.move(steps)
        tile = self.board.get_tile(new_position)

        print(f"🎲 {current_player.name} rolled {dice_result['dice']} = {steps}")
        print(f"📍 Moved from {old_position} to {new_position}: {tile['name']}")

        # Handle tile effect
        result = await self.handle_tile_effect(current_player, tile)
        self.has_rolled = True

        # Check game over
        if await self.check_game_over():
            return {
                "type": TYPE_INFO,
                "message": f"🎲 {current_player.name} rolled {steps}",
                "dice": dice_result,
                "tile": tile,
                "result": result
            }

        # Broadcast update
        await self.broadcast({
            "type": TYPE_INFO,
            "event": EVENT_UPDATE_BOARD,
            "board": self.get_board_state(),
            "currentTurn": current_player.id,
            "diceResult": dice_result,
            "playerMoved": {
                "playerId": player_id,
                "from": old_position,
                "to": new_position,
                "tile": tile
            },
            "message": f"🎲 {current_player.name} rolled {dice_result['dice'][0]}+{dice_result['dice'][1]} = {steps}"
        })

        return {
            "type": TYPE_INFO,
            "message": f"🎲 {current_player.name} rolled {steps}",
            "dice": dice_result,
            "tile": tile,
            "result": result
        }

    async def handle_tile_effect(self, player: Player, tile: dict):
        """Xử lý hiệu ứng ô đất"""
        tile_type = tile["type"]
        
        if tile_type == "property" and tile.get("owner") and tile["owner"] != player.id:
            # Trả tiền thuê
            rent = tile.get("rent", 0)
            owner = self.players.get(tile["owner"])
            if owner:
                success = player.pay_rent(owner, rent)
                if success:
                    await self.broadcast({
                        "type": TYPE_INFO,
                        "event": "playerPaidRent",
                        "fromPlayer": player.id,
                        "toPlayer": owner.id,
                        "amount": rent,
                        "property": tile["name"],
                        "message": f"💰 {player.name} paid ${rent} rent to {owner.name}"
                    })
                return {"action": "paid_rent", "amount": rent, "success": success}
                
        elif tile_type == "tax":
            # Trả thuế
            amount = tile.get("amount", 0)
            player.money -= amount
            await self.broadcast({
                "type": TYPE_INFO,
                "event": "playerPaidTax",
                "playerId": player.id,
                "amount": amount,
                "tile": tile["name"],
                "message": f"💸 {player.name} paid ${amount} tax"
            })
            return {"action": "paid_tax", "amount": amount}
            
        elif tile_type == "go":
            # Qua ô Start
            player.money += 200
            await self.broadcast({
                "type": TYPE_INFO,
                "event": "playerPassedGo",
                "playerId": player.id,
                "amount": 200,
                "message": f"🎉 {player.name} passed GO and collected $200"
            })
            return {"action": "passed_go", "amount": 200}
            
        return {"action": "landed", "tile": tile["name"]}

    async def handle_buy_property(self, player_id: str):
        """Xử lý mua property"""
        player = self.players.get(player_id)
        if not player:
            return {"type": TYPE_ERROR, "message": "Player not found"}
            
        tile = self.board.get_tile(player.position)
        
        if tile.get("owner") is not None:
            return {"type": TYPE_ERROR, "message": "Property already owned"}
            
        if tile.get("type") not in ["property", "railroad", "utility"]:
            return {"type": TYPE_ERROR, "message": "Cannot buy this tile"}
            
        if player.money < tile["price"]:
            return {"type": TYPE_ERROR, "message": "Not enough money"}
            
        # Mua property
        if player.buy_property(tile["name"], tile["price"]):
            tile["owner"] = player_id
            
            await self.broadcast({
                "type": TYPE_INFO,
                "event": "propertyBought",
                "playerId": player_id,
                "property": tile["name"],
                "price": tile["price"],
                "message": f"🏠 {player.name} bought {tile['name']} for ${tile['price']}"
            })
            
            await self.broadcast({
                "type": TYPE_INFO,
                "event": EVENT_UPDATE_BOARD,
                "board": self.get_board_state(),
                "currentTurn": self.get_current_player().id if self.get_current_player() else None
            })
            
            return {
                "type": TYPE_INFO, 
                "message": f"✅ {player.name} bought {tile['name']} for ${tile['price']}"
            }
        else:
            return {"type": TYPE_ERROR, "message": "Purchase failed"}

    async def check_game_over(self) -> bool:
        """Kiểm tra game kết thúc"""
        active_players = [p for p in self.players.values() if not p.is_bankrupt]
        
        if len(active_players) == 1:
            # Có người thắng
            self.winner = active_players[0]
            self.state = STATE_ENDED
            
            await self.broadcast({
                "type": TYPE_INFO,
                "event": EVENT_GAME_OVER,
                "winner": self.winner.to_dict(),
                "message": f"🎉 {self.winner.name} wins the game!"
            })
            
            print(f"🏆 Game over in room {self.room_id}. Winner: {self.winner.name}")
            return True
            
        return False

    def get_board_state(self):
        """Lấy trạng thái board"""
        player_positions = {pid: player.position for pid, player in self.players.items()}
        
        return {
            "players": [player.to_dict() for player in self.players.values()],
            "currentTurn": self.get_current_player().id if self.get_current_player() else None,
            "playerPositions": player_positions,
            "roomState": self.state,
            "roomName": self.room_name,
            "roomId": self.room_id
        }

    def get_room_info(self):
        """Lấy thông tin room"""
        return {
            "roomId": self.room_id,
            "roomName": self.room_name,
            "playerCount": len(self.players),
            "maxPlayers": MAX_PLAYERS,
            "state": self.state,
            "players": [player.name for player in self.players.values()]
        }

    async def broadcast(self, message: dict):
        """Gửi message đến tất cả players trong room"""
        if not self.players:
            return
            
        disconnected_players = []
        for player in self.players.values():
            if player.websocket and not player.websocket.closed:
                try:
                    await player.websocket.send(json.dumps(message))
                except Exception as e:
                    print(f"❌ Failed to send message to {player.name}: {e}")
                    disconnected_players.append(player.id)
            else:
                disconnected_players.append(player.id)
        
        # Remove disconnected players
        for player_id in disconnected_players:
            self.remove_player(player_id)