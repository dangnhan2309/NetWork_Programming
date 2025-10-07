"""
🎮 Monopoly UDP Multicast Client - Phiên bản HOÀN CHỈNH
Tương thích chuẩn Packet 1.0

---------------------------------------------------------
📘 Cách sử dụng:
1️⃣ Chạy server multicast (ví dụ MonopolyMulticastServer)
2️⃣ Chạy client:
    python monopoly_client_multicast.py

3️⃣ Chọn:
   - "Tạo phòng" → tự động sinh group multicast (VD: 239.255.42.101:5007)
   - "Tham gia phòng" → nhập IP nhóm & room ID
---------------------------------------------------------
"""

import asyncio
import socket
import struct
import json
import os
import random
import uuid
import datetime
from typing import Dict, Optional
from ..ui.monopoly_ui import MonopolyUI 

MULTICAST_BASE_IP = "239.255.42."
BASE_PORT = 5007


class MonopolyMulticastClient:
    def __init__(self):
        self.player_name: Optional[str] = None
        self.room_id: Optional[str] = None
        self.room_name: Optional[str] = None
        self.group_ip: Optional[str] = None
        self.port = BASE_PORT
        self.sock: Optional[socket.socket] = None
        self.loop = asyncio.get_event_loop()
        self.is_host = False
        self.ui = MonopolyUI(self)
        self.seq_id = 0
        self.should_exit = False

    # =======================================================
    # 🧱 KHỞI TẠO & MENU
    # =======================================================
    async def run(self):
        print("🎮 MONOPOLY MULTICAST CLIENT")
        print("=============================")

        while not self.should_exit:
            self.display_main_menu()
            choice = input("👉 Chọn [1-3]: ").strip()
            if choice == "1":
                await self.create_room()
            elif choice == "2":
                await self.join_room()
            elif choice == "3":
                print("👋 Tạm biệt!")
                self.should_exit = True
                break
            else:
                print("❌ Lựa chọn không hợp lệ.")
                await asyncio.sleep(1)

    def display_main_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🎯 MONOPOLY MULTICAST CLIENT")
        print("=" * 45)
        print("1. 🏠 Tạo phòng mới (Host)")
        print("2. 🚪 Tham gia phòng có sẵn")
        print("3. ❌ Thoát")
        print("=" * 45)

    # =======================================================
    # 🏠 TẠO PHÒNG / JOIN
    # =======================================================
    async def create_room(self):
        self.player_name = input("👤 Nhập tên của bạn: ").strip() or f"Player{random.randint(100,999)}"
        self.room_name = input("🏠 Tên phòng: ").strip() or f"Room-{random.randint(1000,9999)}"
        self.room_id = f"ROOM_{random.randint(1000,9999)}"
        self.group_ip = MULTICAST_BASE_IP + str(random.randint(101, 199))
        self.is_host = True

        print(f"✅ Phòng '{self.room_name}' tạo thành công!")
        print(f"🌐 Multicast group: {self.group_ip}:{self.port}")
        print(f"🆔 Room ID: {self.room_id}")

        await self.join_multicast_group()
        await self.lobby_loop()

    async def join_room(self):
        self.player_name = input("👤 Nhập tên của bạn: ").strip() or f"Player{random.randint(100,999)}"
        self.room_id = input("🆔 Nhập mã phòng: ").strip()
        self.group_ip = input("🌐 Nhập multicast IP (VD: 239.255.42.101): ").strip()
        self.is_host = False

        if not self.room_id or not self.group_ip:
            print("❌ Thiếu thông tin phòng.")
            return

        await self.join_multicast_group()
        await self.lobby_loop()

    # =======================================================
    # 🔗 MULTICAST SOCKET
    # =======================================================
    async def join_multicast_group(self):
        """Khởi tạo socket multicast"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.sock.bind(('', self.port))
        except OSError:
            print(f"⚠️ Port {self.port} đang được sử dụng, thử lại sau.")
            return

        mreq = struct.pack("4sl", socket.inet_aton(self.group_ip), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setblocking(False)

        print(f"📡 Đã tham gia group multicast {self.group_ip}:{self.port}")

        # Tạo task nhận dữ liệu song song
        self.loop.create_task(self.listen_multicast())

    async def listen_multicast(self):
        """Lắng nghe tin nhắn multicast"""
        while not self.should_exit:
            try:
                data, addr = await self.loop.sock_recv(self.sock, 1024)
                msg = json.loads(data.decode('utf-8'))
                await self.handle_packet(msg, addr)
            except Exception:
                await asyncio.sleep(0.1)

    async def send_packet(self, packet: Dict):
        """Gửi packet tới group"""
        try:
            packet_json = json.dumps(packet).encode('utf-8')
            await self.loop.sock_sendall(self.sock, packet_json)
        except Exception as e:
            print(f"❌ Lỗi gửi gói tin: {e}")

    # =======================================================
    # 📦 PACKET TẠO / XỬ LÝ
    # =======================================================
    def make_packet(self, action: str, data: dict = None, target: str = "ALL", ptype="COMMAND"):
        """Tạo packet chuẩn 1.0"""
        self.seq_id += 1
        packet = {
            "header": {
                "packet_id": str(uuid.uuid4()),
                "room_id": self.room_id,
                "sender": self.player_name,
                "target": target,
                "type": ptype,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "version": "1.0"
            },
            "meta": {
                "seq_id": self.seq_id,
                "ack": False,
                "reliable": False,
                "hop_count": 1
            },
            "command": {
                "action": action,
                "args": data or {}
            },
            "payload": {
                "status": "OK",
                "message": ""
            }
        }
        return packet

    async def handle_packet(self, msg: Dict, addr):
        """Xử lý gói tin nhận được"""
        header = msg.get("header", {})
        room = header.get("room_id")
        if room != self.room_id:
            return  # bỏ qua gói khác phòng

        sender = header.get("sender")
        cmd = msg.get("command", {}).get("action")
        payload = msg.get("payload", {})

        if sender == self.player_name:
            return  # bỏ qua gói tự mình gửi

        # Các loại command xử lý cơ bản
        if cmd == "CHAT":
            content = payload.get("message", "")
            self.ui.display_chat(sender, content)
        elif cmd == "JOIN":
            name = msg["command"]["args"].get("name")
            print(f"👥 {name} đã tham gia phòng!")
        elif cmd == "ROLL":
            dice = msg["payload"]["data"].get("dice", [])
            print(f"🎲 {sender} tung ra {dice}")
        elif cmd == "STATE":
            state = msg["payload"]["data"]
            self.ui.update_game_state(state)
            self.ui.display_game_state()
        else:
            print(f"📩 Nhận gói tin {cmd} từ {sender}")

    # =======================================================
    # 🕹️ LOBBY LOOP
    # =======================================================
    async def lobby_loop(self):
        print("\n💬 Nhập /help để xem lệnh.")
        while not self.should_exit:
            cmd = input("👉 ").strip().lower()
            if cmd == "/exit":
                self.should_exit = True
                break
            elif cmd.startswith("/chat "):
                msg = cmd.replace("/chat ", "")
                packet = self.make_packet("CHAT", {}, "ALL", "CHAT")
                packet["payload"]["message"] = msg
                await self.send_packet(packet)
            elif cmd == "/roll":
                dice = [random.randint(1, 6), random.randint(1, 6)]
                packet = self.make_packet("ROLL", {"dice": dice}, "ALL", "EVENT")
                packet["payload"]["data"] = {"dice": dice}
                await self.send_packet(packet)
            elif cmd == "/help":
                print("""
📘 LỆNH HỖ TRỢ:
 /chat <nội dung>   → gửi tin nhắn đến phòng
 /roll               → tung xúc xắc
 /exit               → rời phòng
                """)
            else:
                print("❌ Lệnh không hợp lệ.")

        print("🚪 Rời phòng và đóng socket...")
        if self.sock:
            self.sock.close()
