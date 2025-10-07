# """
# Client Monopoly Network Handler - Phiên bản chủ phòng HOÀN CHỈNH & TƯƠNG THÍCH SERVER 15.x
# """

# import asyncio
# import websockets
# import json
# import os
# import random
# from typing import Optional, Dict, List
# from . import commands
# from .ui import MonopolyUI


# class MonopolyClient:
#     def __init__(self):
#         self.uri = None
#         self.websocket = None
#         self.player_name = None
#         self.player_id = None
#         self.room_id = None
#         self.room_name = None
#         self.connected = False
#         self.game_state = None
#         self.should_exit = False
#         self.in_game = False
#         self.ui = MonopolyUI(self)
#         self.reconnect_attempts = 0
#         self.max_reconnect_attempts = 3
#         self.is_host = False
#         self.max_players = 4
#         self.required_players = 2
#         self.current_players = 1

#     async def run(self):
#         print("🎮 MONOPOLY CLIENT")
#         print("==================")

#         await self.show_connection_menu()
#         if self.should_exit:
#             return

#         if not await self.connect_to_server():
#             print("❌ Không thể kết nối đến server.")
#             input("Nhấn Enter để thoát...")
#             return

#         await self.main_menu_loop()

#     async def show_connection_menu(self):
#         """Hiển thị menu kết nối"""
#         while True:
#             os.system('cls' if os.name == 'nt' else 'clear')
#             print("🎮 MONOPOLY CLIENT - KẾT NỐI SERVER")
#             print("==================================================")
#             print("1. Kết nối localhost")
#             print("2. Nhập IP server")
#             print("3. Thoát")
#             print("==================================================")

#             choice = input("👉 Chọn [1-3]: ").strip()
#             if choice == "1":
#                 self.uri = "ws://localhost:12345"
#                 break
#             elif choice == "2":
#                 ip = input("👉 Nhập địa chỉ IP server: ").strip() or "localhost"
#                 self.uri = f"ws://{ip}:12345"
#                 break
#             elif choice == "3":
#                 self.should_exit = True
#                 return
#             else:
#                 print("❌ Lựa chọn không hợp lệ.")
#                 await asyncio.sleep(1)

#     async def connect_to_server(self):
#         """Kết nối websocket"""
#         self.reconnect_attempts = 0
#         while self.reconnect_attempts < self.max_reconnect_attempts:
#             try:
#                 print(f"🔄 Đang kết nối ({self.reconnect_attempts + 1}/3)...")
#                 self.websocket = await websockets.connect(
#                     self.uri, ping_interval=20, ping_timeout=10
#                 )
#                 self.connected = True
#                 print("✅ Kết nối thành công!")

#                 asyncio.create_task(self.listen_server())
#                 asyncio.create_task(self.keep_alive())
#                 return True

#             except Exception as e:
#                 print(f"❌ Lỗi: {e}")
#                 self.reconnect_attempts += 1
#                 await asyncio.sleep(2)
#         return False

#     async def main_menu_loop(self):
#         while not self.should_exit:
#             self.display_main_menu()
#             choice = input("👉 Chọn [1-4]: ").strip()
#             if choice == "1":
#                 await self.create_room_flow()
#             elif choice == "2":
#                 await self.join_random_room()
#             elif choice == "3":
#                 await self.join_room_by_id()
#             elif choice == "4":
#                 self.should_exit = True
#             else:
#                 print("❌ Lựa chọn không hợp lệ.")
#                 await asyncio.sleep(1)

#     def display_main_menu(self):
#         os.system('cls' if os.name == 'nt' else 'clear')
#         print("🎮 MONOPOLY MULTIPLAYER")
#         print("=" * 50)
#         print("1. Tạo phòng mới")
#         print("2. Tham gia phòng ngẫu nhiên")
#         print("3. Nhập mã phòng")
#         print("4. Thoát")
#         print("=" * 50)

#     async def create_room_flow(self):
#         """Tạo phòng"""
#         print("\n🏠 TẠO PHÒNG MỚI")
#         self.player_name = input("👉 Tên của bạn: ").strip()
#         if not self.player_name:
#             print("❌ Tên không được trống.")
#             return
#         self.room_name = input("👉 Tên phòng: ").strip() or f"Phòng-{random.randint(1000,9999)}"

#         while True:
#             count = input("👥 Số người (2-4): ").strip()
#             if count in ["2", "3", "4"]:
#                 self.max_players = int(count)
#                 break
#             print("❌ Chỉ được nhập từ 2-4.")

#         msg = {
#             "type": "create_room",
#             "playerName": self.player_name,
#             "roomName": self.room_name,
#             "maxPlayers": self.max_players
#         }
#         await self.send_message(msg)
#         print("📤 Đang tạo phòng...")

#     async def join_random_room(self):
#         """Tạm thời chỉ báo lỗi vì server chưa hỗ trợ random"""
#         print("⚠️ Tính năng này chưa được hỗ trợ trên server.")
#         await asyncio.sleep(1)

#     async def join_room_by_id(self):
#         """Tham gia phòng"""
#         self.player_name = input("👉 Tên của bạn: ").strip() or f"Player{random.randint(1000,9999)}"
#         room_id = input("👉 Mã phòng: ").strip()
#         if not room_id:
#             print("❌ Mã phòng trống.")
#             return

#         msg = {
#             "type": "join_room",
#             "playerName": self.player_name,
#             "roomId": room_id
#         }
#         await self.send_message(msg)
#         print("📤 Đang tham gia phòng...")

#     async def listen_server(self):
#         """Nhận tin nhắn"""
#         while self.connected and not self.should_exit:
#             try:
#                 msg = await self.websocket.recv()
#                 data = json.loads(msg)
#                 await self.handle_server_message(data)
#             except websockets.ConnectionClosed:
#                 print("🔌 Mất kết nối server.")
#                 self.connected = False
#                 break
#             except Exception as e:
#                 print(f"⚠️ Lỗi nhận: {e}")
#                 break

#     async def handle_server_message(self, data):
#         """Xử lý message"""
#         t = data.get("type")
#         if t == "info":
#             self.player_id = data.get("playerId", self.player_id)
#             print("✅", data.get("message", ""))
#         elif t == "room_created":
#             self.room_id = data.get("roomId")
#             self.is_host = True
#             print(f"🎉 Phòng tạo thành công: {self.room_name} ({self.room_id})")
#             await self.wait_in_room()
#         elif t == "joined_room":
#             self.room_id = data.get("roomId")
#             print(f"✅ Đã tham gia phòng {self.room_id}")
#             await self.wait_in_room()
#         elif t == "error":
#             print(f"❌ {data.get('message')}")

#     async def wait_in_room(self):
#         """Màn hình chờ"""
#         while not self.should_exit:
#             os.system('cls' if os.name == 'nt' else 'clear')
#             print("🎮 PHÒNG CHỜ MONOPOLY")
#             print("=" * 40)
#             print(f"🏠 {self.room_name} ({self.room_id})")
#             print(f"👤 {'Chủ phòng' if self.is_host else self.player_name}")
#             print("=" * 40)
#             print("📜 Lệnh: /exit để rời phòng")
#             cmd = input("👉 ").strip().lower()
#             if cmd == "/exit":
#                 await self.cleanup_room_state()
#                 break

#     async def send_message(self, message: dict):
#         """Gửi message"""
#         try:
#             await self.websocket.send(json.dumps(message))
#             return True
#         except Exception as e:
#             print(f"❌ Lỗi gửi: {e}")
#             return False

#     async def keep_alive(self):
#         """Giữ ping/pong"""
#         while self.connected:
#             await asyncio.sleep(15)
#             try:
#                 pong = await self.websocket.ping()
#                 await pong
#             except Exception:
#                 self.connected = False
#                 break

#     async def cleanup_room_state(self):
#         self.room_id = None
#         self.room_name = None
#         self.is_host = False
#         print("🧹 Đã rời khỏi phòng.")
