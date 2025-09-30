import asyncio
import json
import websockets
from .game_manager import GameManager
from src.shared import constants as C
from src.shared import utils as U

class MonopolyServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = {}  # websocket -> player_name
        self.game_manager = GameManager()
        self.game_manager.set_broadcast_callback(self.broadcast_to_all)

    async def handler(self, websocket):
        """Xử lý kết nối từ client"""
        player_name = None
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    cmd = data.get("cmd")
                    payload = data.get("data", {})
                    
                    if cmd == "join":
                        name = payload.get("name", "Unknown")
                        if self.game_manager.add_player(name, websocket):
                            player_name = name
                            self.clients[websocket] = name
                            await self.send(websocket, "info", f"Welcome {name}! Waiting for game to start...")
                            await self.send(websocket, "game_state", self.game_manager.get_game_state())
                        else:
                            await self.send(websocket, "error", "Cannot join game (game full or name taken)")
                            
                    elif cmd == "roll":
                        if player_name:
                            result = self.game_manager.handle_player_action(player_name, "ROLL")
                            await self.send(websocket, "action_result", result)
                        else:
                            await self.send(websocket, "error", "You must join game first")
                            
                    elif cmd == "buy":
                        if player_name:
                            result = self.game_manager.handle_player_action(player_name, "BUY")
                            await self.send(websocket, "action_result", result)
                        else:
                            await self.send(websocket, "error", "You must join game first")
                            
                    elif cmd == "end_turn":
                        if player_name:
                            result = self.game_manager.handle_player_action(player_name, "END_TURN")
                            await self.send(websocket, "action_result", result)
                        else:
                            await self.send(websocket, "error", "You must join game first")
                            
                    elif cmd == "state":
                        await self.send(websocket, "game_state", self.game_manager.get_game_state())
                        
                    elif cmd == "help":
                        help_text = (
                            "📖 DANH SÁCH LỆNH:\n"
                            "/join <tên>    - Tham gia game\n"
                            "/roll          - Đổ xúc xắc\n" 
                            "/buy           - Mua đất\n"
                            "/end_turn      - Kết thúc lượt\n"
                            "/state         - Xem trạng thái game\n"
                            "/help          - Xem trợ giúp\n"
                            "/quit          - Thoát game\n"
                        )
                        await self.send(websocket, "info", help_text)
                        
                    elif cmd == "quit":
                        break
                        
                    else:
                        await self.send(websocket, "error", f"Unknown command: {cmd}")
                        
                except json.JSONDecodeError:
                    await self.send(websocket, "error", "Invalid JSON format")
                except Exception as e:
                    await self.send(websocket, "error", f"Server error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Connection closed for {player_name}")
        finally:
            # Cleanup khi client disconnect
            if player_name:
                self.game_manager.remove_player(player_name)
            if websocket in self.clients:
                del self.clients[websocket]
            await self.broadcast_state()

    async def send(self, websocket, msg_type, payload):
        """Gửi message tới client"""
        try:
            if not isinstance(payload, dict):
                payload = {"message": str(payload)}
                
            message = {
                "type": msg_type,
                "timestamp": asyncio.get_event_loop().time(),
                **payload
            }
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"❌ Send error to {self.clients.get(websocket, 'unknown')}: {e}")

    async def broadcast_to_all(self, message):
        """Broadcast message tới tất cả clients"""
        if not self.clients:
            return
            
        if isinstance(message, dict):
            message_data = message
        else:
            message_data = {"message": str(message)}
            
        full_message = {
            "type": "broadcast",
            "timestamp": asyncio.get_event_loop().time(),
            **message_data
        }
        
        message_json = json.dumps(full_message)
        disconnected = []
        
        for websocket, player_name in self.clients.items():
            try:
                await websocket.send(message_json)
            except Exception as e:
                print(f"❌ Broadcast failed to {player_name}: {e}")
                disconnected.append(websocket)
        
        # Cleanup disconnected clients
        for websocket in disconnected:
            player_name = self.clients.get(websocket)
            if player_name:
                self.game_manager.remove_player(player_name)
            del self.clients[websocket]

    async def broadcast_state(self):
        """Broadcast game state tới tất cả clients"""
        state = self.game_manager.get_game_state()
        await self.broadcast_to_all({
            "type": "game_state",
            "state": state
        })

    async def start(self):
        """Khởi động server"""
        print("🚀 Starting Monopoly Server...")
        print(f"📡 Server will run on ws://{self.host}:{self.port}")
        print("👥 Waiting for players to connect...")
        print("🛑 Press Ctrl+C to stop server\n")
        
        async with websockets.serve(self.handler, self.host, self.port):
            # Hiển thị trạng thái ban đầu
            self.game_manager.display_game_state()
            await asyncio.Future()  # run forever