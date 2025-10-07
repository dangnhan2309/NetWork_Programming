"""
🎮 MonopolyClient - Client UDP Multicast cho game Monopoly nhiều người chơi

CÁCH DÙNG:
---------
1️⃣ Chạy client:
    python -m client.client_main

2️⃣ Khi được hỏi tên, nhập tên người chơi (VD: Alice)

3️⃣ Gõ lệnh trong console:
    /chat Hello      → Gửi tin nhắn đến tất cả
    /roll            → Tung xúc xắc
    /buy             → Mua property
    /end             → Kết thúc lượt
    /exit            → Thoát game

4️⃣ Tất cả tin nhắn & cập nhật game được gửi/nhận qua UDP multicast.
"""
import asyncio
import json
import socket
import struct
from ..core import commands
from ..ui.monopoly_ui import MonopolyUI
from ...shared.constants import MULTICAST_GROUP, MULTICAST_PORT, BUFFER_SIZE, ENCODING

class MonopolyClient:
    def __init__(self):
        self.sock = None
        self.ui = MonopolyUI(self)
        self.player_name = None

    async def join_multicast_group(self):
        """Tham gia nhóm multicast UDP"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", MULTICAST_PORT))

        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.sock.setblocking(False)

        print(f"✅ Đã tham gia nhóm multicast {MULTICAST_GROUP}:{MULTICAST_PORT}")

    async def run(self):
        await self.join_multicast_group()
        loop = asyncio.get_event_loop()
        loop.create_task(self.receive_messages())

        self.player_name = input("👤 Nhập tên người chơi: ").strip()
        self.ui.set_player_name(self.player_name)
        await self.send_message({
            "type": "join",
            "name": self.player_name
        })

        # Vòng lặp nhập lệnh người chơi
        while True:
            cmd_text = input("> ")
            msg, err = commands.parse_cmd(cmd_text)
            if err:
                self.ui.display_message(err, "error")
                continue
            if msg is None:
                break
            await self.send_message(msg)

    async def send_message(self, msg: dict):
        """Gửi message đến nhóm multicast"""
        data = json.dumps(msg).encode(ENCODING)
        self.sock.sendto(data, (MULTICAST_GROUP, MULTICAST_PORT))

    async def receive_messages(self):
        """Lắng nghe các message multicast"""
        loop = asyncio.get_event_loop()
        while True:
            try:
                data, _ = await loop.run_in_executor(None, self.sock.recvfrom, BUFFER_SIZE)
                msg = json.loads(data.decode(ENCODING))

                msg_type = msg.get("type")
                if msg_type == "state_update":
                    self.ui.update_game_state(msg.get("state", {}))
                    self.ui.display_game_state()
                elif msg_type == "chat":
                    self.ui.display_message(f"{msg.get('name')}: {msg.get('message')}", "broadcast")
                elif msg_type == "info":
                    self.ui.display_message(msg.get("message", ""), "info")
            except Exception:
                await asyncio.sleep(0.1)
