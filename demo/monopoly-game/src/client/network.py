import asyncio
import json
import websockets
from src.shared import constants as C
from src.shared.protocol import Protocol
from .commands import parse_cmd
from .ui import MonopolyUI

class MonopolyClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.player_name = None
        self.ui = MonopolyUI(self)
        self.connected = False

    async def connect(self):
        """Kết nối đến server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self.ui.display_message("✅ Đã kết nối đến server!", "success")
            return True
        except Exception as e:
            self.ui.display_message(f"❌ Không thể kết nối đến server: {e}", "error")
            return False

    async def run(self):
        """Chạy client"""
        self.ui.display_welcome()
        
        if not await self.connect():
            return

        try:
            # Chạy đồng thời: lắng nghe server và gửi input
            await asyncio.gather(
                self.listen_server(),
                self.send_input()
            )
        except websockets.exceptions.ConnectionClosed:
            self.ui.display_message("🔌 Mất kết nối với server", "error")
        except Exception as e:
            self.ui.display_message(f"❌ Lỗi: {e}", "error")
        finally:
            self.connected = False

    async def listen_server(self):
        """Lắng nghe message từ server"""
        async for raw_message in self.websocket:
            try:
                data = json.loads(raw_message)
                await self.handle_server_message(data)
            except json.JSONDecodeError:
                self.ui.display_message("⚠️ Nhận được tin nhắn lỗi từ server", "warning")
            except Exception as e:
                self.ui.display_message(f"❌ Lỗi xử lý tin nhắn: {e}", "error")

    async def handle_server_message(self, raw_data):
        """Xử lý message từ server mà không cần chỉnh server"""
        try:
            # Nếu nhận string -> bọc thành dict để tránh lỗi .get()
            if isinstance(raw_data, str):
                data = {"type": "info", "message": raw_data}
            elif isinstance(raw_data, dict):
                data = raw_data
            else:
                self.ui.display_message(f"📩 Nhận dữ liệu không hợp lệ: {raw_data}", "warning")
                return

            # Đảm bảo data là dict và có key 'type'
            if not isinstance(data, dict):
                self.ui.display_message(f"⚠️ Dữ liệu không phải dict: {data}", "warning")
                return

            msg_type = data.get("type", "info")

            if msg_type == "info":
                message = data.get("message", "No message")
                self.ui.display_message(message, "info")

            elif msg_type == "error":
                message = data.get("message", "Unknown error")
                self.ui.display_message(message, "error")

            elif msg_type == "game_state":
                state = data.get("state", {})
                if isinstance(state, dict):
                    self.ui.update_game_state(state)
                    self.ui.display_game_state()
                else:
                    self.ui.display_message(f"🟡 Trạng thái game: {state}", "info")

            elif msg_type == "action_result":
                result = data.get("message", "Action completed")
                self.ui.display_message(result, "success")

            elif msg_type == "broadcast":
                message = data.get("message", "Broadcast")
                self.ui.display_message(message, "broadcast")

            elif msg_type == "chat":
                sender = data.get("sender", "Unknown")
                message = data.get("message", "")
                self.ui.display_chat(sender, message)

            else:
                self.ui.display_message(f"📦 Server: {data}", "debug")

        except Exception as e:
            self.ui.display_message(f"❌ ❌ Lỗi xử lý tin nhắn: {e} | raw_data: {raw_data}", "error")


    async def send_input(self):
        """Gửi input từ người dùng đến server"""
        while self.connected:
            try:
                # Sử dụng UI để lấy input
                user_input = await self.ui.get_input_async()
                
                if not user_input:
                    continue
                    
                # Parse command
                message, error = parse_cmd(user_input)
                
                if error:
                    self.ui.display_message(error, "error")
                    continue
                    
                if not message:
                    continue

                # Gửi message đến server
                await self.send_message(message)
                
            except KeyboardInterrupt:
                self.ui.display_message("👋 Thoát game...", "info")
                break
            except Exception as e:
                self.ui.display_message(f"❌ Lỗi gửi tin nhắn: {e}", "error")

    async def send_message(self, message: dict):
        """Gửi message đến server"""
        if not self.websocket:
            self.ui.display_message("❌ Chưa kết nối đến server", "error")
            return
            
        try:
            # Chuyển đổi message thành packet theo protocol của server
            cmd = message.get(C.K_TYPE, "").lower()
            data = {k: v for k, v in message.items() if k != C.K_TYPE}
            
            packet = {
                "cmd": cmd,
                "data": data
            }
            
            await self.websocket.send(json.dumps(packet))
            
        except Exception as e:
            self.ui.display_message(f"❌ Lỗi gửi tin nhắn: {e}", "error")

    async def join_game(self, name: str):
        """Tham gia game với tên"""
        self.player_name = name
        self.ui.set_player_name(name)
        await self.send_message(C.m_join(name))

    async def send_chat(self, message: str):
        """Gửi tin nhắn chat"""
        await self.send_message(C.m_chat(message))

    async def roll_dice(self):
        """Gieo xúc xắc"""
        await self.send_message(C.m_roll())

    async def buy_property(self):
        """Mua property"""
        await self.send_message(C.m_buy())

    async def end_turn(self):
        """Kết thúc lượt"""
        await self.send_message(C.m_end_turn())

    async def request_state(self):
        """Yêu cầu trạng thái game"""
        await self.send_message(C.m_state_ping())

    async def exit_game(self):
        """Thoát game"""
        await self.send_message(C.m_exit())
        self.connected = False


async def main():
    """Hàm main để chạy client"""
    import sys
    
    # Lấy URI từ command line hoặc dùng mặc định
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    
    client = MonopolyClient(uri)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    asyncio.run(main())