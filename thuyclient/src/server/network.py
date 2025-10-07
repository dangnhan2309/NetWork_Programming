"""
Server Network Handler - Phiên bản hoàn chỉnh & tương thích websockets 15.x
"""

import asyncio
import websockets
import json
import uuid
from typing import Dict, Optional
from . import room_manager
from ..shared import constants as C

SEND_TIMEOUT = 5  # Giới hạn thời gian gửi message


class ServerNetwork:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.room_manager = room_manager.RoomManager()
        # connected_clients: player_id -> {websocket, player_id, player_name, room_id (optional)}
        self.connected_clients: Dict[str, dict] = {}

    # =========================================================
    # 🟢 HÀM KHỞI ĐỘNG SERVER
    # =========================================================
    async def start_server(self):
        """Khởi động WebSocket server"""
        print("🌐 MONOPOLY WEBSOCKET SERVER CONFIGURATION")
        print("=" * 50)
        print(f"📍 Local IP: {self.get_local_ip()}")
        print(f"📍 Port: {self.port}")
        print(f"📡 Connect: ws://{self.get_local_ip()}:{self.port}")
        print("=" * 50)
        print("⚠️  Đảm bảo firewall cho phép kết nối trên port 12345!")
        print("=" * 50)

        # Chạy cleanup task
        asyncio.create_task(self.room_manager.periodic_cleanup())

        # Khởi chạy WebSocket server
        server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
            max_size=None,
        )

        print("🎮 MONOPOLY SERVER - MULTIPLAYER EDITION")
        print(f"📍 ws://localhost:{self.port}")
        print(f"📍 ws://{self.get_local_ip()}:{self.port}")
        print("👥 Players: 2-4 per room")
        print("=" * 50)
        print("✅ Server is running... Press Ctrl+C to stop")
        print("=" * 50)

        await server.wait_closed()

    # =========================================================
    # 🟢 HÀM XỬ LÝ KẾT NỐI CLIENT
    # =========================================================
    async def handler(self, websocket, path):
        """Xử lý kết nối client"""
        player_id = str(uuid.uuid4())[:8]
        player_info = {
            'websocket': websocket,
            'player_id': player_id,
            'player_name': None,
            'room_id': None
        }
        self.connected_clients[player_id] = player_info

        try:
            # Gửi welcome message
            welcome_msg = {
                "type": C.TYPE_INFO,
                "message": "✅ Connected to Monopoly Server!",
                "playerId": player_id
            }
            await asyncio.wait_for(websocket.send(json.dumps(welcome_msg)), timeout=SEND_TIMEOUT)
            print(f"🟢 Player connected: {player_id}")

            # Lắng nghe các message từ client
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📩 Received from {player_id}: {data}")

                    # Cập nhật tên người chơi nếu có
                    maybe_name = data.get('playerName')
                    if maybe_name:
                        self.connected_clients[player_id]['player_name'] = maybe_name

                    # Xử lý message
                    response = await self.handle_message(data, websocket, player_id)
                    if response:
                        await asyncio.wait_for(websocket.send(json.dumps(response)), timeout=SEND_TIMEOUT)

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": C.TYPE_ERROR,
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    print(f"⚠️ Error processing message from {player_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Client disconnected: {player_id}")
        except Exception as e:
            print(f"❌ Handler error for {player_id}: {e}")
        finally:
            await self.handle_disconnect(websocket, player_id)

    # =========================================================
    # 🟡 XỬ LÝ MESSAGE
    # =========================================================
    async def handle_message(self, data: dict, websocket, player_id: str) -> Optional[dict]:
        """Xử lý từng loại message từ client"""
        msg_type = data.get("type")

        # Tạo phòng mới
        if msg_type == C.TYPE_CREATE_ROOM:
            return await self.handle_create_room(data, websocket, player_id)

        # Tham gia phòng
        elif msg_type == C.TYPE_JOIN_ROOM:
            return await self.handle_join_room(data, websocket, player_id)

        # Rời phòng
        elif msg_type == C.TYPE_LEAVE_ROOM:
            return await self.handle_leave_room(data, websocket, player_id)

        # Ping
        elif msg_type == C.TYPE_PING:
            return {"type": C.TYPE_PONG, "message": "pong"}

        # Mặc định
        else:
            return {"type": C.TYPE_ERROR, "message": f"Unknown message type: {msg_type}"}

    # =========================================================
    # 🟢 HÀM TẠO PHÒNG
    # =========================================================
    async def handle_create_room(self, data: dict, websocket, player_id: str) -> dict:
        room_name = data.get("roomName", f"Room-{uuid.uuid4().hex[:4]}")
        max_players = data.get("maxPlayers", 4)

        room = self.room_manager.create_room(room_name, max_players)
        self.connected_clients[player_id]['room_id'] = room.room_id
        room.add_player(player_id, websocket)

        print(f"🏠 Player {player_id} created room {room.room_id} ({room_name})")

        return {
            "type": C.TYPE_ROOM_CREATED,
            "roomId": room.room_id,
            "roomName": room_name,
            "maxPlayers": max_players
        }

    # =========================================================
    # 🟢 HÀM JOIN PHÒNG
    # =========================================================
    async def handle_join_room(self, data: dict, websocket, player_id: str) -> dict:
        room_id = data.get("roomId")
        room = self.room_manager.get_room(room_id)
        if not room:
            return {"type": C.TYPE_ERROR, "message": "Room not found"}

        if room.is_full():
            return {"type": C.TYPE_ERROR, "message": "Room is full"}

        room.add_player(player_id, websocket)
        self.connected_clients[player_id]['room_id'] = room_id
        print(f"👥 Player {player_id} joined room {room_id}")

        return {"type": C.TYPE_JOINED_ROOM, "roomId": room_id, "players": room.get_player_list()}

    # =========================================================
    # 🔴 HÀM RỜI PHÒNG
    # =========================================================
    async def handle_leave_room(self, data: dict, websocket, player_id: str) -> dict:
        room_id = self.connected_clients[player_id].get("room_id")
        if not room_id:
            return {"type": C.TYPE_ERROR, "message": "Player not in a room"}

        room = self.room_manager.get_room(room_id)
        if room:
            room.remove_player(player_id)

        self.connected_clients[player_id]['room_id'] = None
        print(f"🚪 Player {player_id} left room {room_id}")
        return {"type": C.TYPE_LEFT_ROOM, "roomId": room_id}

    # =========================================================
    # ⚫ NGẮT KẾT NỐI
    # =========================================================
    async def handle_disconnect(self, websocket, player_id: str):
        """Xử lý khi client ngắt kết nối"""
        info = self.connected_clients.pop(player_id, None)
        if not info:
            return

        room_id = info.get("room_id")
        if room_id:
            room = self.room_manager.get_room(room_id)
            if room:
                room.remove_player(player_id)
                print(f"🔴 Player {player_id} disconnected from room {room_id}")

    # =========================================================
    # ⚙️ HÀM HỖ TRỢ
    # =========================================================
    def get_local_ip(self):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
