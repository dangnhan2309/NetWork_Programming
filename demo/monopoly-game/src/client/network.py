<<<<<<< Updated upstream

# src/client/network.py
import socket
import threading
from typing import Callable
from ..shared.protocol import encode,decode
class ClientNetwork:
    def __init__(self, host='127.0.0.1', port=12345, on_message: Callable[[dict], None]=None):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.on_message = on_message
        self.recv_thread = None
        self.running = False

    def connect(self):
        self.sock.connect((self.host, self.port))
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def _recv_loop(self):
        buf = b''
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    pkt = decode(line + b'\n')
                    if pkt and self.on_message:
                        self.on_message(pkt)
            except Exception:
                break
        self.running = False
=======
import asyncio
import json
import websockets
from src.shared import constants as C
from .commands import parse_cmd
from .ui import MonopolyUI

class MonopolyClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.player_name = None
        self.ui = MonopolyUI(self)
        self.connected = False
        self.pending_join_name = None  # Tên đang chờ join

    async def connect(self):
        """Kết nối đến server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self.ui.display_connection_status(True)
            return True
        except Exception as e:
            self.connected = False
            self.ui.display_message(f"Không thể kết nối đến server: {e}", "error")
            return False

    async def run(self):
        """Chạy client"""
        self.ui.display_welcome()
        
        if not await self.connect():
            return

        try:
            await asyncio.gather(
                self.listen_server(),
                self.send_input()
            )
        except websockets.exceptions.ConnectionClosed:
            self.ui.display_connection_status(False)
        except Exception as e:
            self.ui.display_message(f"Lỗi: {e}", "error")
        finally:
            self.connected = False
            self.ui.display_connection_status(False)

    async def listen_server(self):
        """Lắng nghe message từ server"""
        async for raw_message in self.websocket:
            try:
                data = json.loads(raw_message)
                await self.handle_server_message(data)
            except json.JSONDecodeError:
                self.ui.display_message("Nhận được tin nhắn lỗi từ server", "warning")
            except Exception as e:
                self.ui.display_message(f"Lỗi xử lý tin nhắn: {e}", "error")

    async def handle_server_message(self, raw_data):
        """Xử lý message từ server với format thân thiện"""
        try:
            # Xử lý dữ liệu đầu vào
            if isinstance(raw_data, str):
                data = {"type": "info", "message": raw_data}
            elif isinstance(raw_data, dict):
                data = raw_data
            else:
                self.ui.display_message(f"Nhận dữ liệu không hợp lệ: {raw_data}", "warning")
                return

            if not isinstance(data, dict):
                return

            msg_type = data.get("type", "info")

            if msg_type == "info":
                message = data.get("message", "No message")
                # Kiểm tra nếu đây là kết quả roll ẩn trong info message
                if "rolled" in message.lower() and "dice" in data:
                    # Đây là kết quả roll từ server
                    dice = data.get("dice", {})
                    player = message.split(" rolled")[0] if " rolled" in message else "Someone"
                    if dice:
                        self.ui.display_message(f"🎲 {player} gieo xúc xắc: {dice.get('dice', [0, 0])[0]} + {dice.get('dice', [0, 0])[1]} = {dice.get('total', 0)}", "success")
                        if player == self.player_name:
                            self.ui.mark_rolled()
                    await self.request_state()
                else:
                    self.ui.display_message(message, "info")
                    
                # Tự động extract player name từ welcome message
                if "Welcome" in message and "!" in message:
                    name_part = message.split("Welcome ")[1].split("!")[0]
                    if name_part and not self.player_name:
                        self.player_name = name_part
                        self.ui.set_player_name(name_part)
                
                # Hoặc từ pending join
                elif self.pending_join_name and "joined" in message.lower():
                    self.player_name = self.pending_join_name
                    self.ui.set_player_name(self.pending_join_name)
                    self.pending_join_name = None

            elif msg_type == "error":
                message = data.get("message", "Unknown error")
                self.ui.display_message(message, "error")
                # Reset pending join nếu có lỗi
                if self.pending_join_name:
                    self.pending_join_name = None

            elif msg_type == "game_state":
                state = data.get("state", {})
                if isinstance(state, dict):
                    self.ui.update_game_state(state)
                    self.ui.display_game_state()
                else:
                    self.ui.display_message(f"Cập nhật trạng thái game: {state}", "info")

            elif msg_type == "action_result":
                result = data.get("result", {})
                message = data.get("message", "Action completed")
                
                # Xử lý kết quả roll
                if result.get("dice"):
                    dice = result["dice"]
                    self.ui.display_message(f"🎲 Bạn đã gieo: {dice['dice'][0]} + {dice['dice'][1]} = {dice['total']}", "success")
                    self.ui.mark_rolled()
                
                # Xử lý kết quả mua property
                elif "bought" in message.lower():
                    self.ui.display_message(message, "success")
                
                else:
                    self.ui.display_message(message, "success")
                
                # Làm mới trạng thái sau hành động
                await self.request_state()

            elif msg_type == "broadcast":
                # Xử lý broadcast message có thể chứa game state
                if "state" in data and "current_turn" in data and "players" in data:
                    # Đây thực sự là game state được broadcast
                    state = {
                        "state": data.get("state"),
                        "current_turn": data.get("current_turn"),
                        "players": data.get("players")
                    }
                    self.ui.update_game_state(state)
                    self.ui.display_game_state()
                else:
                    message = data.get("message", "Broadcast")
                    self.ui.display_message(message, "broadcast")

            elif msg_type == "player_joined":
                player_name = data.get("player_name", "Someone")
                self.ui.display_message(f"{player_name} đã tham gia game", "broadcast")
                await self.request_state()

            elif msg_type == "player_left":
                player_name = data.get("player_name", "Someone")
                self.ui.display_message(f"{player_name} đã rời game", "broadcast")
                await self.request_state()

            elif msg_type == "dice_rolled":
                player = data.get("player", "Someone")
                dice1 = data.get("dice1", 0)
                dice2 = data.get("dice2", 0)
                total = data.get("total", 0)
                if player != self.player_name:
                    self.ui.display_message(f"🎲 {player} gieo xúc xắc: {dice1} + {dice2} = {total}", "broadcast")

            elif msg_type == "player_moved":
                player = data.get("player", "Someone")
                from_pos = data.get("from_pos", 0)
                to_pos = data.get("to_pos", 0)
                if player != self.player_name:
                    self.ui.display_message(f"📍 {player} di chuyển từ {from_pos} đến {to_pos}", "broadcast")

            elif msg_type == "property_bought":
                player = data.get("player", "Someone")
                property_name = data.get("property", "property")
                price = data.get("price", 0)
                self.ui.display_message(f"💰 {player} đã mua {property_name} với giá ${price}", "broadcast")

            elif msg_type == "turn_started":
                player = data.get("player", "Someone")
                if self.player_name and player.lower() == self.player_name.lower():
                    self.ui.display_message("🎲 Đến lượt của bạn! Gõ /roll để bắt đầu", "success")
                    self.ui.reset_turn_state()
                else:
                    self.ui.display_message(f"⏰ Đến lượt của {player}", "info")
                await self.request_state()

            elif msg_type == "game_started":
                self.ui.display_message("🎉 Game đã bắt đầu!", "success")
                await self.request_state()

            elif msg_type == "chat":
                sender = data.get("sender", "Unknown")
                message = data.get("message", "")
                self.ui.display_chat(sender, message)

            else:
                # Kiểm tra nếu đây là game state ẩn trong các message khác
                if "state" in data and "players" in data:
                    self.ui.update_game_state(data)
                    self.ui.display_game_state()
                else:
                    self.ui.display_message(f"Dữ liệu từ server: {data}", "debug")

        except Exception as e:
            self.ui.display_message(f"Lỗi xử lý tin nhắn: {e} | raw_data: {raw_data}", "error")

    async def send_input(self):
        """Gửi input từ người dùng đến server"""
        while self.connected:
            try:
                user_input = await self.ui.get_input_async()
                
                if not user_input:
                    continue
                    
                # Hiển thị help nếu người dùng gõ /help
                if user_input.lower() == "/help":
                    self.ui.display_help()
                    continue
                    
                # Parse command
                message, error = parse_cmd(user_input)
                
                if error:
                    self.ui.display_message(error, "error")
                    continue
                    
                if not message:
                    continue

                # Đặc biệt xử lý lệnh JOIN - set pending name
                if message.get(C.K_TYPE) == C.JOIN:
                    name = message.get(C.K_NAME)
                    if name:
                        self.pending_join_name = name

                # Kiểm tra lượt chơi trước khi gửi lệnh game
                if message.get(C.K_TYPE) in [C.ROLL, C.BUY, C.END_TURN]:
                    if not await self.validate_turn(message[C.K_TYPE]):
                        continue

                # Gửi message đến server
                await self.send_message(message)
                
            except KeyboardInterrupt:
                self.ui.display_message("Thoát game...", "info")
                break
            except Exception as e:
                self.ui.display_message(f"Lỗi gửi tin nhắn: {e}", "error")

    async def validate_turn(self, action_type: str) -> bool:
        """Kiểm tra xem có phải lượt của người chơi không"""
        if not self.player_name:
            self.ui.display_message("❌ Bạn chưa tham gia game. Hãy dùng /join <tên> để tham gia trước.", "error")
            return False
            
        if not self.ui.game_state:
            self.ui.display_message("❌ Chưa có thông tin trạng thái game. Vui lòng chờ server cập nhật...", "error")
            return False
            
        game_status = self.ui.game_state.get("state", "").upper()
        if game_status != "PLAYING":
            self.ui.display_message(f"❌ Game chưa bắt đầu. Trạng thái hiện tại: {game_status}", "error")
            return False
            
        current_turn_idx = self.ui.game_state.get("current_turn", 0)
        players = self.ui.game_state.get("players", [])
        
        if not players or current_turn_idx >= len(players):
            self.ui.display_message("❌ Lỗi: Không thể xác định lượt chơi", "error")
            return False
            
        current_player = players[current_turn_idx]["name"]
        
        # DEBUG: Hiển thị thông tin để kiểm tra
        print(f"🔧 DEBUG VALIDATE: Current player from server: '{current_player}'")
        print(f"🔧 DEBUG VALIDATE: My player name: '{self.player_name}'")
        print(f"🔧 DEBUG VALIDATE: Are they equal? {current_player.lower() == self.player_name.lower()}")
        print(f"🔧 DEBUG VALIDATE: Current turn index: {current_turn_idx}")
        print(f"🔧 DEBUG VALIDATE: All players: {[p['name'] for p in players]}")
        
        # So sánh không phân biệt hoa thường để tránh lỗi
        if current_player.lower() != self.player_name.lower():
            self.ui.display_message(f"❌ Không phải lượt của bạn! Hiện tại là lượt của {current_player}", "error")
            return False
            
        # Kiểm tra riêng cho lệnh roll
        if action_type == C.ROLL and self.ui.has_rolled_this_turn:
            self.ui.display_message("❌ Bạn đã gieo xúc xắc trong lượt này rồi!", "error")
            return False
            
        return True
>>>>>>> Stashed changes

    def send(self, packet: dict):
        try:
<<<<<<< Updated upstream
            self.sock.sendall(encode(packet))
=======
            # Xử lý đặc biệt cho các loại message
            if "cmd" in message:
                # Message đã có cmd (như lệnh state)
                packet = message
            else:
                # Message theo protocol C (JOIN, ROLL, etc.)
                cmd = message.get(C.K_TYPE, "").lower()
                data = {k: v for k, v in message.items() if k != C.K_TYPE}
                
                packet = {
                    "cmd": cmd,
                    "data": data
                }
            
            print(f"🔧 DEBUG NETWORK: Sending packet: {packet}")
            await self.websocket.send(json.dumps(packet))
            
>>>>>>> Stashed changes
        except Exception as e:
            print("[CLIENT] send error:", e)

<<<<<<< Updated upstream
    def close(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
=======
    async def request_state(self):
        """Yêu cầu trạng thái game - sử dụng lệnh 'state'"""
        try:
            packet = {
                "cmd": "state",
                "data": {}
            }
            await self.websocket.send(json.dumps(packet))
        except Exception as e:
            self.ui.display_message(f"❌ Lỗi yêu cầu trạng thái: {e}", "error")

    async def exit_game(self):
        """Thoát game"""
        await self.send_message(C.m_exit())
        self.connected = False


async def main():
    """Hàm main để chạy client"""
    import sys
    
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    
    client = MonopolyClient(uri)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        client.ui.display_message("👋 Tạm biệt!", "info")
    except Exception as e:
        client.ui.display_message(f"❌ Lỗi: {e}", "error")


if __name__ == "__main__":
    asyncio.run(main())
>>>>>>> Stashed changes
