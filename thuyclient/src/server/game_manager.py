"""
Game Room với State Machine - Phiên bản đầy đủ với chủ phòng
"""

import asyncio
import random
import json
from typing import Dict, List, Optional
from .board import Board
from .player import Player
from ..shared import constants as C

class GameRoom:
    def __init__(self, room_id: str, room_name: str = "Phòng chơi", max_players: int = None):
        self.room_id = room_id
        self.room_name = room_name
        self.players: Dict[str, dict] = {}
        self.board = Board()
        self.state = C.STATE_EMPTY
        self.current_turn_index = 0
        self.has_rolled = False
        self.winner = None
        self.host_id = None
        self.max_players = max_players or C.MAX_PLAYERS
        self.required_players = C.MIN_PLAYERS
        
        print(f"🏠 Room created: {room_name} (ID: {room_id}), Max players: {self.max_players}")

    def add_player(self, player_id: str, player_name: str, websocket, is_host: bool = False):
        """Thêm player vào phòng"""
        if not hasattr(self, 'players'):
            self.players = {}
        
        # Kiểm tra nếu phòng đã đầy
        if len(self.players) >= self.max_players:
            return False
        
        # Tạo player object
        player_data = {
            'id': player_id,
            'name': player_name,
            'websocket': websocket,
            'money': 1500,
            'position': 0,
            'properties': [],
            'is_host': is_host,
            'is_ready': False
        }
        
        # Thêm vào dictionary
        self.players[player_id] = player_data
        
        # Nếu là player đầu tiên hoặc được chỉ định là host, đặt làm host
        if len(self.players) == 1 or is_host:
            self.host_id = player_id
            self.players[player_id]['is_host'] = True
        
        print(f"🔧 DEBUG: Đã thêm player {player_name} (ID: {player_id})")
        print(f"🔧 DEBUG: Tổng players: {len(self.players)}/{self.max_players}")
        
        # Cập nhật trạng thái phòng
        if len(self.players) >= C.MIN_PLAYERS:
            self.state = C.STATE_WAITING
        else:
            self.state = C.STATE_EMPTY
            
        return True

    def remove_player(self, player_id: str):
        """Xóa player khỏi phòng"""
        if not hasattr(self, 'players') or player_id not in self.players:
            return
            
        player_name = self.players[player_id].get('name', 'Unknown')
        del self.players[player_id]
        
        # Nếu host rời đi, chọn host mới
        if self.host_id == player_id and self.players:
            new_host_id = next(iter(self.players.keys()))
            self.host_id = new_host_id
            self.players[new_host_id]['is_host'] = True
            print(f"👑 Chuyển quyền host cho: {self.players[new_host_id]['name']}")
        elif not self.players:
            self.host_id = None
        
        print(f"🔧 DEBUG: Đã xóa player {player_name} (ID: {player_id})")
        print(f"🔧 DEBUG: Còn lại {len(self.players)} players")
        
        # Cập nhật trạng thái phòng
        if len(self.players) == 0:
            self.state = C.STATE_EMPTY
        elif len(self.players) < C.MIN_PLAYERS:
            self.state = C.STATE_WAITING

    def can_start_game(self) -> bool:
        """Kiểm tra có thể bắt đầu game không"""
        return len(self.players) >= self.required_players and self.state == C.STATE_WAITING

    async def start_game(self):
        """Bắt đầu game"""
        if self.can_start_game():
            self.state = C.STATE_PLAYING
            self.current_turn_index = 0
            self.has_rolled = False
            self.winner = None
            
            print(f"🎉 Game started in room {self.room_id} with {len(self.players)} players")
            
            # Broadcast game started
            await self.broadcast({
                "type": C.TYPE_INFO,
                "event": "gameStarted",
                "message": "🎮 Game started!",
                "board": self.get_board_state(),
                "currentTurn": self.get_current_player_id()
            })

    def get_current_player_id(self) -> Optional[str]:
        """Lấy ID của player hiện tại đến lượt"""
        if not self.players or self.state != C.STATE_PLAYING:
            return None
            
        player_ids = list(self.players.keys())
        if not player_ids:
            return None
            
        current_id = player_ids[self.current_turn_index % len(player_ids)]
        return current_id

    def get_current_player(self) -> Optional[dict]:
        """Lấy player hiện tại đến lượt"""
        player_id = self.get_current_player_id()
        return self.players.get(player_id) if player_id else None

    def next_turn(self):
        """Chuyển lượt"""
        if not self.players or self.state != C.STATE_PLAYING:
            return
            
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        self.has_rolled = False
        
        current_player = self.get_current_player()
        if current_player:
            print(f"🎲 Turn changed to: {current_player['name']} in room {self.room_id}")

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
        if not current_player or current_player['id'] != player_id:
            return {"type": C.TYPE_ERROR, "message": "❌ Not your turn!"}

        if self.has_rolled:
            return {"type": C.TYPE_ERROR, "message": "❌ Already rolled this turn!"}

        # Roll dice
        dice_result = self.roll_dice()
        steps = dice_result["total"]
        
        # Move player
        old_position = current_player['position']
        new_position = (old_position + steps) % len(self.board.tiles)
        current_player['position'] = new_position
        tile = self.board.get_tile(new_position)

        print(f"🎲 {current_player['name']} rolled {dice_result['dice']} = {steps}")
        print(f"📍 Moved from {old_position} to {new_position}: {tile['name']}")

        # Handle tile effect
        result = await self.handle_tile_effect(current_player, tile)
        self.has_rolled = True

        # Check game over
        if await self.check_game_over():
            return {
                "type": C.TYPE_INFO,
                "message": f"🎲 {current_player['name']} rolled {steps}",
                "dice": dice_result,
                "tile": tile,
                "result": result
            }

        # Broadcast update
        await self.broadcast({
            "type": C.TYPE_INFO,
            "event": C.EVENT_UPDATE_BOARD,
            "board": self.get_board_state(),
            "currentTurn": self.get_current_player_id(),
            "diceResult": dice_result,
            "playerMoved": {
                "playerId": player_id,
                "from": old_position,
                "to": new_position,
                "tile": tile
            },
            "message": f"🎲 {current_player['name']} rolled {dice_result['dice'][0]}+{dice_result['dice'][1]} = {steps}"
        })

        return {
            "type": C.TYPE_INFO,
            "message": f"🎲 {current_player['name']} rolled {steps}",
            "dice": dice_result,
            "tile": tile,
            "result": result
        }

    async def handle_tile_effect(self, player: dict, tile: dict):
        """Xử lý hiệu ứng ô đất"""
        tile_type = tile.get("type", "")
        
        if tile_type == "property" and tile.get("owner") and tile["owner"] != player['id']:
            # Trả tiền thuê
            rent = tile.get("rent", 0)
            owner = self.players.get(tile["owner"])
            if owner and player['money'] >= rent:
                player['money'] -= rent
                owner['money'] += rent
                await self.broadcast({
                    "type": C.TYPE_INFO,
                    "event": "playerPaidRent",
                    "fromPlayer": player['id'],
                    "toPlayer": owner['id'],
                    "amount": rent,
                    "property": tile["name"],
                    "message": f"💰 {player['name']} paid ${rent} rent to {owner['name']}"
                })
                return {"action": "paid_rent", "amount": rent, "success": True}
            else:
                return {"action": "paid_rent", "amount": rent, "success": False}
                
        elif tile_type == "tax":
            # Trả thuế
            amount = tile.get("amount", 0)
            if player['money'] >= amount:
                player['money'] -= amount
                await self.broadcast({
                    "type": C.TYPE_INFO,
                    "event": "playerPaidTax",
                    "playerId": player['id'],
                    "amount": amount,
                    "tile": tile["name"],
                    "message": f"💸 {player['name']} paid ${amount} tax"
                })
                return {"action": "paid_tax", "amount": amount, "success": True}
            else:
                return {"action": "paid_tax", "amount": amount, "success": False}
            
        elif tile_type == "go":
            # Qua ô Start
            player['money'] += 200
            await self.broadcast({
                "type": C.TYPE_INFO,
                "event": "playerPassedGo",
                "playerId": player['id'],
                "amount": 200,
                "message": f"🎉 {player['name']} passed GO and collected $200"
            })
            return {"action": "passed_go", "amount": 200}
            
        return {"action": "landed", "tile": tile["name"]}

    async def handle_buy_property(self, player_id: str):
        """Xử lý mua property"""
        player = self.players.get(player_id)
        if not player:
            return {"type": C.TYPE_ERROR, "message": "Player not found"}
            
        tile = self.board.get_tile(player['position'])
        
        if tile.get("owner") is not None:
            return {"type": C.TYPE_ERROR, "message": "Property already owned"}
            
        if tile.get("type") not in ["property", "railroad", "utility"]:
            return {"type": C.TYPE_ERROR, "message": "Cannot buy this tile"}
            
        if player['money'] < tile["price"]:
            return {"type": C.TYPE_ERROR, "message": "Not enough money"}
            
        # Mua property
        player['money'] -= tile["price"]
        player['properties'].append(tile["name"])
        tile["owner"] = player_id
            
        await self.broadcast({
            "type": C.TYPE_INFO,
            "event": "propertyBought",
            "playerId": player_id,
            "property": tile["name"],
            "price": tile["price"],
            "message": f"🏠 {player['name']} bought {tile['name']} for ${tile['price']}"
        })
        
        await self.broadcast({
            "type": C.TYPE_INFO,
            "event": C.EVENT_UPDATE_BOARD,
            "board": self.get_board_state(),
            "currentTurn": self.get_current_player_id()
        })
        
        return {
            "type": C.TYPE_INFO, 
            "message": f"✅ {player['name']} bought {tile['name']} for ${tile['price']}"
        }

    async def check_game_over(self) -> bool:
        """Kiểm tra game kết thúc"""
        active_players = [p for p in self.players.values() if p['money'] > 0]
        
        if len(active_players) == 1:
            # Có người thắng
            self.winner = active_players[0]
            self.state = C.STATE_ENDED
            
            await self.broadcast({
                "type": C.TYPE_INFO,
                "event": C.EVENT_GAME_OVER,
                "winner": {
                    "id": self.winner['id'],
                    "name": self.winner['name'],
                    "money": self.winner['money']
                },
                "message": f"🎉 {self.winner['name']} wins the game!"
            })
            
            print(f"🏆 Game over in room {self.room_id}. Winner: {self.winner['name']}")
            return True
            
        return False

    def get_board_state(self):
        """Lấy trạng thái board"""
        players_list = []
        for player_data in self.players.values():
            players_list.append({
                'id': player_data['id'],
                'name': player_data['name'],
                'money': player_data['money'],
                'position': player_data['position'],
                'properties': player_data['properties'],
                'is_host': player_data.get('is_host', False)
            })
        
        return {
            "players": players_list,
            "currentTurn": self.get_current_player_id(),
            "roomState": self.state,
            "roomName": self.room_name,
            "roomId": self.room_id,
            "maxPlayers": self.max_players,
            "requiredPlayers": self.required_players
        }

    def get_room_info(self):
        """Lấy thông tin room"""
        player_names = [player_data['name'] for player_data in self.players.values()]
        host_name = None
        if self.host_id and self.host_id in self.players:
            host_name = self.players[self.host_id]['name']
        
        return {
            "roomId": self.room_id,
            "roomName": self.room_name,
            "playerCount": len(self.players),
            "maxPlayers": self.max_players,
            "requiredPlayers": self.required_players,
            "state": self.state,
            "players": player_names,
            "host": host_name
        }

    async def broadcast(self, message: dict):
        """Gửi message đến tất cả players trong room - SỬA LỖI WEBSOCKET"""
        if not hasattr(self, 'players') or not self.players:
            return
            
        disconnected_players = []
        
        for player_id, player_data in self.players.items():
            websocket = player_data.get('websocket')
            if websocket:
                try:
                    # Sửa lỗi: Kiểm tra trạng thái websocket đúng cách
                    if hasattr(websocket, 'closed') and not websocket.closed:
                        await websocket.send(json.dumps(message))
                    else:
                        disconnected_players.append(player_id)
                except Exception as e:
                    print(f"❌ Failed to send message to {player_data.get('name')}: {e}")
                    disconnected_players.append(player_id)
            else:
                disconnected_players.append(player_id)
        
        # Remove disconnected players
        for player_id in disconnected_players:
            self.remove_player(player_id)