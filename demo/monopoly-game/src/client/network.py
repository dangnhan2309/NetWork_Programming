"""
Client Network Handler - Phiên bản ổn định
"""

import asyncio
import websockets
import json
import os
import random
from typing import Optional, Dict, List

class MonopolyClient:
    def __init__(self, uri="ws://localhost:12345"):
        self.uri = uri
        self.websocket = None
        self.player_name = None
        self.player_id = None
        self.room_id = None
        self.room_name = None
        self.connected = False
        self.game_state = None
        self.available_rooms = []
        self.should_exit = False
        self.input_queue = asyncio.Queue()

    async def connect(self):
        """Kết nối đến server"""
        try:
            self.websocket = await websockets.connect(
                self.uri, 
                ping_interval=20, 
                ping_timeout=10,
                close_timeout=10
            )
            self.connected = True
            self.display_message("✅ Đã kết nối đến server!", "success")
            return True
        except Exception as e:
            self.display_message(f"❌ Không thể kết nối đến server: {e}", "error")
            return False

    async def run(self):
        """Chạy client chính"""
        if not await self.connect():
            return

        try:
            # Tạo task độc lập cho input
            input_task = asyncio.create_task(self.handle_user_input())
            listen_task = asyncio.create_task(self.listen_server())
            
            # Hiển thị menu chính
            await self.show_main_menu()
            
            # Chờ các task hoàn thành
            await asyncio.gather(input_task, listen_task, return_exceptions=True)
            
        except Exception as e:
            self.display_message(f"❌ Lỗi: {e}", "error")
        finally:
            await self.cleanup()

    async def show_main_menu(self):
        """Hiển thị menu chính"""
        while self.connected and not self.room_id and not self.should_exit:
            self.clear_screen()
            self.display_header("🎲 MONOPOLY MULTIPLAYER")
            
            print("🏠 MENU CHÍNH:")
            print("1. Tạo phòng chơi mới")
            print("2. Tham gia phòng ngẫu nhiên") 
            print("3. Thoát")
            print()
            
            choice = input("👉 Chọn [1-3]: ").strip()
            
            if choice == "1":
                await self.create_room_flow()
            elif choice == "2":
                await self.join_random_room()
            elif choice == "3":
                self.should_exit = True
                return
            else:
                self.display_message("❌ Lựa chọn không hợp lệ!", "error")
                await asyncio.sleep(1)
            
           

    async def create_room_flow(self):
        """Luồng tạo phòng mới"""
        self.clear_screen()
        self.display_header("🏠 TẠO PHÒNG MỚI")
        
        try:
            if not self.player_name:
                self.player_name = input("👉 Nhập tên của bạn: ").strip()
                if not self.player_name:
                    self.player_name = "Player" + str(random.randint(1000, 9999))

            room_name = input("👉 Tên phòng: ").strip()
            if not room_name:
                room_name = f"Phòng của {self.player_name}"

            # Nhập tên phòng
            await self.input_queue.put("room_prompt")
            room_name = await self.get_input_from_queue("👉 Tên phòng: ")
            if not room_name:
                room_name = f"Phòng của {self.player_name}"
                
            # Tạo phòng
            await self.send_message({
                "action": "createRoom",
                "playerName": self.player_name,
                "roomName": room_name
            })
            
            self.display_message("⏳ Đang tạo phòng...", "info")
        except Exception as e:
            self.display_message(f"❌ Lỗi tạo phòng: {e}", "error")

    async def join_random_room(self):
        """Tham gia phòng ngẫu nhiên"""
        try:
            if not self.player_name:
                await self.input_queue.put("name_prompt")
                self.player_name = await self.get_input_from_queue("👉 Nhập tên của bạn: ")
                if not self.player_name:
                    self.player_name = "Player" + str(random.randint(1000, 9999))
            
            await self.send_message({
                "action": "joinRandom",
                "playerName": self.player_name
            })
            
            self.display_message("⏳ Đang tìm phòng...", "info")
        except Exception as e:
            self.display_message(f"❌ Lỗi tham gia phòng: {e}", "error")

    async def handle_user_input(self):
        while self.connected and not self.should_exit:
            try:
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, input)
                if user_input.strip():
                    await self.input_queue.put(user_input.strip())
            except (KeyboardInterrupt, EOFError):
                self.should_exit = True
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self.should_exit:
                    self.display_message(f"❌ Lỗi đọc input: {e}", "error")
                await asyncio.sleep(0.1)


    async def get_input_from_queue(self, prompt: str = "") -> str:
        """Lấy input từ queue với timeout an toàn"""
        if prompt:
            print(prompt, end='', flush=True)
        
        try:
            user_input = await asyncio.wait_for(self.input_queue.get(), timeout=3600)
            # Bỏ qua các prompt nội bộ
            if user_input in ["menu_prompt", "name_prompt", "room_prompt"]:
                return ""
            return user_input
        except asyncio.TimeoutError:
            return ""
        except asyncio.CancelledError:
            return ""  # Task bị cancel → trả về rỗng
        except Exception as e:
            self.display_message(f"❌ Lỗi lấy input: {e}", "error")
            return ""


    async def process_game_command(self, command: str):
        """Xử lý lệnh game"""
        if command.lower() == "/help":
            self.show_game_help()
        elif command.lower() == "/exit":
            self.should_exit = True
        elif command.lower() == "/state":
            await self.request_state()
        elif command.startswith("/"):
            # Parse các lệnh khác
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd == "/roll":
                await self.send_message({
                    "action": "rollDice",
                    "playerId": self.player_id
                })
            elif cmd == "/buy":
                await self.send_message({
                    "action": "buy", 
                    "playerId": self.player_id
                })
            elif cmd == "/end":
                await self.send_message({
                    "action": "endTurn",
                    "playerId": self.player_id
                })
            elif cmd in ["/say", "/chat"] and len(parts) > 1:
                message = " ".join(parts[1:])
                await self.send_message({
                    "action": "chat",
                    "message": message
                })
            else:
                self.display_message("❌ Lệnh không hợp lệ! Gõ /help để xem danh sách lệnh", "error")
        else:
            # Gửi chat message
            await self.send_message({
                "action": "chat",
                "message": command
            })

    async def listen_server(self):
        """Lắng nghe message từ server"""
        try:
            async for raw_message in self.websocket:
                if self.should_exit:
                    break
                    
                try:
                    data = json.loads(raw_message)
                    await self.handle_server_message(data)
                except json.JSONDecodeError:
                    self.display_message("❌ Nhận được tin nhắn lỗi từ server", "error")
        except websockets.exceptions.ConnectionClosed:
            if not self.should_exit:
                self.display_message("🔌 Mất kết nối với server", "error")
                self.connected = False
        except Exception as e:
            if not self.should_exit:
                self.display_message(f"❌ Lỗi kết nối: {e}", "error")

    async def handle_server_message(self, data: dict):
        """Xử lý message từ server"""
        msg_type = data.get("type")
        
        if msg_type == "info":
            message = data.get("message", "")
            if message:  # Chỉ hiển thị nếu có message
                self.display_message(message, "info")
            
            # Lưu player_id và room_id
            if "playerId" in data:
                self.player_id = data["playerId"]
            if "roomId" in data and not self.room_id:
                self.room_id = data["roomId"]
                self.room_name = data.get("roomName", "Unknown Room")
                self.display_message(f"🎉 Đã vào phòng '{self.room_name}' thành công!", "success")
                
            # Xử lý events
            event = data.get("event")
            if event == "updateBoard":
                self.game_state = data.get("board", {})
                self.display_game_state()
            elif event == "playerJoined":
                player_name = data.get("player", {}).get("name", "")
                self.display_message(f"🎮 {player_name} đã tham gia phòng", "broadcast")
            elif event == "playerLeft":
                self.display_message(data.get("message", ""), "broadcast")
            elif event == "gameStarted":
                self.display_message("🎮 Game đã bắt đầu!", "success")
                self.game_state = data.get("board", {})
                self.display_game_state()
            elif event == "gameOver":
                winner = data.get("winner", {})
                self.display_message(f"🏆 {winner.get('name', '')} thắng game!", "success")
                # Quay về menu sau khi game kết thúc
                await asyncio.sleep(3)
                self.room_id = None
                self.room_name = None
                
        elif msg_type == "error":
            message = data.get("message", "")
            self.display_message(message, "error")
            
        elif data.get("event") == "chat":
            player_name = data.get("playerName", "")
            message = data.get("message", "")
            if player_name and message:
                print(f"💬 {player_name}: {message}")

    def display_game_state(self):
        """Hiển thị trạng thái game"""
        if not self.game_state:
            return
            
        self.clear_screen()
        self.display_header(f"🎮 {self.game_state.get('roomName', 'MONOPOLY GAME')}")
        
        # Hiển thị thông tin phòng
        room_state = self.game_state.get('roomState', 'Unknown')
        state_display = {
            "WAITING": "⏳ Đang chờ người chơi",
            "PLAYING": "🎮 Đang chơi",
            "ENDED": "🏁 Kết thúc"
        }.get(room_state, room_state)
        
        print(f"🏠 Trạng thái: {state_display}")
        print()
        
        # Hiển thị thông tin người chơi
        players = self.game_state.get("players", [])
        current_turn = self.game_state.get("currentTurn")
        
        print("👥 NGƯỜI CHƠI:")
        print("-" * 50)
        
        for player in players:
            name = player.get("name", "Unknown")
            money = player.get("money", 0)
            position = player.get("position", 0)
            is_bankrupt = player.get("isBankrupt", False)
            
            turn_indicator = " 🎲" if player.get("id") == current_turn else ""
            you_indicator = " 👑 BẠN" if name == self.player_name else ""
            bankrupt_indicator = " 💀" if is_bankrupt else ""
            
            print(f"{you_indicator}{turn_indicator}{bankrupt_indicator} {name}")
            print(f"   💰 ${money:,} | 📍 Vị trí: {position}")
            
            properties = player.get("properties", [])
            if properties:
                print(f"   🏠 Sở hữu: {len(properties)} property(s)")
            print()
        
        # Hiển thị lượt chơi hiện tại
        if current_turn:
            current_player = next((p for p in players if p.get("id") == current_turn), None)
            if current_player:
                if current_player.get("name") == self.player_name:
                    print("🎲 🎲 🎲 ĐẾN LƯỢT BẠN! 🎲 🎲 🎲")
                    print("💡 Gõ /roll để gieo xúc xắc")
                else:
                    print(f"⏰ Đến lượt: {current_player.get('name')}")
        
        print("=" * 50)
        print("💬 Gõ tin nhắn để chat hoặc /help để xem hướng dẫn")

    def show_game_help(self):
        """Hiển thị trợ giúp game"""
        help_text = """
🎮 DANH SÁCH LỆNH TRONG GAME:

🎲 LỆNH GAME:
  /roll          - Gieo xúc xắc và di chuyển
  /buy           - Mua property hiện tại
  /end           - Kết thúc lượt chơi

💬 LỆNH CHAT:
  /say <tin nhắn> - Gửi tin nhắn chat
  /chat <tin nhắn> - Gửi tin nhắn chat
  [tin nhắn thường] - Gõ trực tiếp để chat

📋 LỆNH KHÁC:
  /help          - Hiển thị trợ giúp này
  /exit          - Thoát game
        """
        print(help_text)

    def display_header(self, title: str):
        """Hiển thị header"""
        print("=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)
        print()

    def display_message(self, message: str, msg_type: str = "info"):
        """Hiển thị message"""
        if msg_type == "error":
            print(f"❌ {message}")
        elif msg_type == "success":
            print(f"✅ {message}")
        elif msg_type == "warning":
            print(f"⚠️ {message}")
        elif msg_type == "broadcast":
            print(f"📢 {message}")
        else:
            print(f"ℹ️ {message}")

    def clear_screen(self):
        """Xóa màn hình"""
        os.system('cls' if os.name == 'nt' else 'clear')

    async def send_message(self, message: dict):
        if not self.websocket or not self.connected:
            self.display_message("❌ Chưa kết nối đến server!", "error")
            return
        
        try:
            await self.websocket.send(json.dumps(message))
        except (websockets.ConnectionClosed, AttributeError) as e:
            self.display_message(f"❌ Server error: {e}", "error")
            self.connected = False
        except Exception as e:
            self.display_message(f"❌ Lỗi gửi tin nhắn: {e}", "error")
            self.connected = False


    async def request_state(self):
        """Yêu cầu cập nhật trạng thái"""
        pass

    async def cleanup(self):
        """Dọn dẹp trước khi thoát"""
        self.should_exit = True
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        print("\n👋 Tạm biệt!")


async def main():
    import sys
    
    # Lấy URI từ command line hoặc dùng mặc định
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:12345"
    
    client = MonopolyClient(uri)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")