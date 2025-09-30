
import asyncio
import json
import websockets

from ..shared.protocol import Protocol
from ..shared.Command_list import command_dic
from .ui import ClientUI


class Client:
    def __init__(self, uri="ws://localhost:8765", name="Guest"):
        self.uri = uri
        self.name = name
        self.ui = ClientUI()   # Khởi tạo UI

    async def run(self):
<<<<<<< Updated upstream
        """
           Attempts to connect to a WebSocket server and prints a log message.

           Args:
           """
        try:
            async with websockets.connect(self.uri) as websocket:
                print(f"[CLIENT] Connected to {self.uri} as {self.name}")
                await websocket.send("Hello Client")
                await asyncio.gather(
                    self.user_input_loop(websocket),
                    self.receive_message(websocket),
                )
        except Exception as e :
            print("")

    async def user_input_loop(self, websocket):
        """
        CLI loop cho người chơi nhập lệnh.
        Có thể nhập CHAT, JOIN hoặc chọn command trong command_dic.
        """
        while True:
            raw = await asyncio.to_thread(input, f"{self.name}> ")
            #self.ui.update_map()
            if raw.startswith("TC"):
                pass

            if raw.startswith("CHAT "):
                # Ví dụ: CHAT hello
                msg = raw[5:]
                await self.send_command(websocket, "CHAT", {"message": msg})
                continue

            if raw.startswith("JOIN "):
                # Ví dụ: JOIN Nhan
                nick = raw[5:]
                await self.send_command(websocket, "JOIN", {"name": nick})
                continue

            if raw in command_dic:
                await self.send_command(websocket, raw)
                continue

            print(f"[CLIENT] Unknown input: {raw}")

    async def send_command(self, websocket, key: str, overrides: dict = None):
        """Gửi lệnh Monopoly từ command_dic."""
        if key not in command_dic:
            print(f"[ERROR] Command {key} not found in command_dic")
=======
        """Chạy client"""
        self.ui.display_welcome()
        # hiển thị thêm bàn cờ
        
        if not await self.connect():
>>>>>>> Stashed changes
            return

        # Copy object để không ảnh hưởng đến bản gốc
        msg = json.loads(json.dumps(command_dic[key]))

        if overrides:
            msg["data"].update(overrides)

        packet = Protocol.make_packet(msg["action"], msg["data"])
        await websocket.send(packet)
        print(f"[CLIENT] Sent -> {msg}")

    async def receive_message(self, websocket):
        """Nhận và xử lý message từ server."""
        async for message in websocket:
            packet = Protocol.parse_packet(message)
            action = packet.get("action")
            data = packet.get("data", {})

            print(f"\n[SERVER] {action} {data}")

            # ==== Dùng UI để hiển thị ====
            if action == "GAME_STATE":

                self.ui.update_map(data)
                # hiển thị menu nếu có command gợi ý
                if "available_commands" in data:
                    self.ui.display_commands(data["available_commands"])

            elif action == "ROLL_RESULT":
                print(f"🎲 Dice Result: {data.get('dice', '?')}")

            elif action == "CHAT":
                print(f"[CHAT] {data.get('message')}")

            elif action == "PLAYER_STATUS":
                pid = data.get("player_id", "Unknown")
                status = data.get("status", {})
                self.ui.update_player_status(pid, status)

            elif action == "PROPERTIES":
                self.ui.show_properties(data.get("properties", []))

            elif action == "ERROR":
                print(f"❌ Error: {data.get('msg')}")

<<<<<<< Updated upstream
            # Prompt lại cho user
            print(f"{self.name}> ", end="", flush=True)
=======
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
            #--------------------------------- các command player ---------------
                # nên chuyển thành file khác
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
>>>>>>> Stashed changes


if __name__ == "__main__":
    client = Client(uri="ws://localhost:8765", name="Alice")
    asyncio.run(client.run())

