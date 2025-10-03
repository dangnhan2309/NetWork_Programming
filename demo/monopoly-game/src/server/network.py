"""
WebSocket Server Network Handler
"""

import asyncio
import websockets
import json
import uuid
from typing import Dict
from .room_manager import RoomManager
from ..shared.constants import *


class ServerNetwork:
    def __init__(self, host="0.0.0.0", port=12345):
        self.host = host
        self.port = port
        self.room_manager = RoomManager()
        self.server = None

    async def start(self):
        """Khởi động server"""
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print("🎮 MONOPOLY SERVER - STATE MACHINE EDITION")
        print(f"📍 Listening on ws://{self.host}:{self.port}")
        print(f"👥 Players: {MIN_PLAYERS}-{MAX_PLAYERS} per room")
        print("="*50)
        print("Server is running... Press Ctrl+C to stop")
        print("="*50)
        await self.server.wait_closed()

    async def handler(self, websocket):
        """Xử lý kết nối client"""
        player_info = {"id": None, "name": None, "room_id": None}
        
        try:
            # Gửi welcome message khi client kết nối
            await websocket.send(json.dumps({
                "type": TYPE_INFO,
                "message": "✅ Connected to Monopoly Server!"
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data, player_info)
                    
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    await self.send_error(websocket, f"Server error: {str(e)}")

        except websockets.exceptions.ConnectionClosed:
            print(f"❌ Client disconnected: {player_info['name'] or 'Unknown'}")
        finally:
            await self.handle_disconnect(websocket, player_info)

    async def handle_client_message(self, websocket, data: dict, player_info: dict):
        """Xử lý message từ client"""
        action = data.get("action")
        
        if action == ACTION_CREATE_ROOM:
            await self.handle_create_room(websocket, data, player_info)
            
        elif action == ACTION_JOIN_RANDOM:
            await self.handle_join_random(websocket, data, player_info)
            
        elif action == ACTION_ROLL_DICE:
            await self.handle_game_action(websocket, data, player_info)
            
        elif action == ACTION_BUY:
            await self.handle_buy_action(websocket, data, player_info)
            
        elif action == ACTION_END_TURN:
            await self.handle_end_turn(websocket, data, player_info)
            
        elif action == ACTION_CHAT:
            await self.handle_chat(websocket, data, player_info)
        else:
            await self.send_error(websocket, f"Unknown action: {action}")

    async def handle_create_room(self, websocket, data, player_info):
        """Xử lý tạo phòng"""
        player_name = data.get("playerName", "Player")
        room_name = data.get("roomName", "Phòng mới")
        
        # Tạo player ID
        player_id = str(uuid.uuid4())[:8]
        
        # Tạo phòng mới
        room = self.room_manager.create_room(room_name)
        
        # Thêm player vào phòng
        if room.add_player(player_id, player_name, websocket):
            player_info["id"] = player_id
            player_info["name"] = player_name
            player_info["room_id"] = room.room_id
            
            # Gửi thông báo thành công
            await websocket.send(json.dumps({
                "type": TYPE_INFO,
                "message": f"✅ Created room '{room_name}'",
                "roomId": room.room_id,
                "playerId": player_id,
                "roomName": room.room_name
            }))
            
            # Broadcast player joined
            await room.broadcast({
                "type": TYPE_INFO,
                "event": EVENT_PLAYER_JOINED,
                "player": {"id": player_id, "name": player_name},
                "roomStatus": room.get_room_info(),
                "message": f"🎮 {player_name} joined the room"
            })
            
            # Kiểm tra bắt đầu game
            if room.can_start_game():
                print(f"🚀 Starting game in room {room.room_id}...")
                await room.start_game()
                
        else:
            await self.send_error(websocket, "❌ Cannot create room")

    async def handle_join_random(self, websocket, data, player_info):
        """Xử lý tham gia phòng ngẫu nhiên"""
        player_name = data.get("playerName", "Player")
        player_id = str(uuid.uuid4())[:8]
        
        # Tìm phòng có sẵn
        room = self.room_manager.get_random_available_room()
        if not room:
            # Tạo phòng mới nếu không có
            room = self.room_manager.create_room(f"Phòng của {player_name}")
        
        # Thêm player vào phòng
        if room.add_player(player_id, player_name, websocket):
            player_info["id"] = player_id
            player_info["name"] = player_name
            player_info["room_id"] = room.room_id
            
            await websocket.send(json.dumps({
                "type": TYPE_INFO,
                "message": f"✅ Joined room '{room.room_name}'",
                "roomId": room.room_id,
                "playerId": player_id,
                "roomName": room.room_name
            }))
            
            # Broadcast
            await room.broadcast({
                "type": TYPE_INFO,
                "event": EVENT_PLAYER_JOINED,
                "player": {"id": player_id, "name": player_name},
                "roomStatus": room.get_room_info(),
                "message": f"🎮 {player_name} joined the room"
            })
            
            # Start game nếu đủ điều kiện
            if room.can_start_game():
                print(f"🚀 Starting game in room {room.room_id}...")
                await room.start_game()
                
        else:
            await self.send_error(websocket, "❌ Cannot join room")

    async def handle_game_action(self, websocket, data, player_info):
        """Xử lý hành động game"""
        if not player_info["room_id"]:
            await self.send_error(websocket, "❌ Not in a room")
            return
            
        room = self.room_manager.get_room(player_info["room_id"])
        if not room:
            await self.send_error(websocket, "❌ Room not found")
            return
            
        player_id = player_info["id"]
        action = data.get("action")
        
        if action == ACTION_ROLL_DICE:
            result = await room.handle_roll_dice(player_id)
            await websocket.send(json.dumps(result))
            
        elif action == ACTION_END_TURN:
            room.next_turn()
            current_player = room.get_current_player()
            if current_player:
                await room.broadcast({
                    "type": TYPE_INFO,
                    "event": EVENT_UPDATE_BOARD,
                    "board": room.get_board_state(),
                    "currentTurn": current_player.id,
                    "message": f"🔄 {player_info['name']} ended turn. Now it's {current_player.name}'s turn!"
                })

    async def handle_buy_action(self, websocket, data, player_info):
        """Xử lý mua property"""
        if not player_info["room_id"]:
            await self.send_error(websocket, "❌ Not in a room")
            return
            
        room = self.room_manager.get_room(player_info["room_id"])
        if not room:
            await self.send_error(websocket, "❌ Room not found")
            return
            
        result = await room.handle_buy_property(player_info["id"])
        await websocket.send(json.dumps(result))

    async def handle_chat(self, websocket, data, player_info):
        """Xử lý chat"""
        if not player_info["room_id"]:
            await self.send_error(websocket, "❌ Not in a room")
            return
            
        room = self.room_manager.get_room(player_info["room_id"])
        if not room:
            await self.send_error(websocket, "❌ Room not found")
            return
            
        message = data.get("message", "")
        await room.broadcast({
            "type": TYPE_INFO,
            "event": ACTION_CHAT,
            "playerId": player_info["id"],
            "playerName": player_info["name"],
            "message": message
        })

    async def handle_disconnect(self, websocket, player_info):
        """Xử lý ngắt kết nối"""
        if player_info["room_id"]:
            room = self.room_manager.get_room(player_info["room_id"])
            if room:
                room.remove_player(player_info["id"])
                
                # Broadcast player left
                await room.broadcast({
                    "type": TYPE_INFO,
                    "event": EVENT_PLAYER_LEFT,
                    "playerId": player_info["id"],
                    "message": f"🚪 {player_info['name']} left the game",
                    "roomStatus": room.get_room_info()
                })
        
        self.room_manager.remove_empty_rooms()

    async def send_error(self, websocket, message: str):
        """Gửi lỗi"""
        await websocket.send(json.dumps({
            "type": TYPE_ERROR,
            "message": message
        }))

    async def stop(self):
        """Dừng server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        print("🛑 Server stopped")