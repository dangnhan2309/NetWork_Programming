import asyncio
import socket
import struct
import json
from typing import Optional, Dict, Callable


class MulticastClient:
    def __init__(self):
        self.udp_socket: Optional[socket.socket] = None
        self.group_ip: Optional[str] = None
        self.port: Optional[int] = None
        self.room_id: Optional[str] = None
        self.running = False
        self._receive_task: Optional[asyncio.Task] = None
        self._message_handlers: Dict[str, Callable] = {}
        self.client = None  # Liên kết với game client

    async def join_multicast_group(self, multicast_ip: str, port: int, room_id: str, retry_count: int = 2) -> bool:
        for attempt in range(retry_count + 1):
            try:
                self.group_ip = multicast_ip or "239.0.0.10"
                self.port = port or 5225 + (hash(room_id) % 1000)
                self.room_id = room_id

                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # Bind socket
                self.udp_socket.bind(('', self.port))
                mreq = struct.pack("4sL", socket.inet_aton(self.group_ip), socket.INADDR_ANY)
                self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                self.udp_socket.setblocking(False)

                self.running = True
                self._receive_task = asyncio.create_task(self._receive_messages())
                print(f"✅ Joined multicast {self.group_ip}:{self.port}")
                return True
            except Exception as e:
                print(f"⚠️ Lỗi multicast (attempt {attempt+1}): {e}")
                await self.cleanup()
                await asyncio.sleep(1)
        return False

    async def send_packet(self, packet: Dict) -> bool:
        if not self.udp_socket or not self.group_ip or not self.port:
            print("❌ Chưa kết nối multicast")
            return False
        try:
            packet.setdefault("header", {})["room_id"] = self.room_id
            data = json.dumps(packet).encode('utf-8')
            loop = asyncio.get_event_loop()
            await loop.sock_sendto(self.udp_socket, data, (self.group_ip, self.port))
            return True
        except Exception as e:
            print(f"❌ Lỗi gửi multicast: {e}")
            return False

    async def _receive_messages(self):
        loop = asyncio.get_event_loop()
        while self.running and self.udp_socket:
            try:
                data, addr = await loop.sock_recvfrom(self.udp_socket, 4096)
                await self._handle_packet(data, addr)
            except (BlockingIOError, asyncio.CancelledError):
                await asyncio.sleep(0.01)
            except Exception as e:
                print(f"⚠️ Lỗi nhận multicast: {e}")
                await asyncio.sleep(0.1)

    async def _handle_packet(self, data: bytes, addr: tuple):
        try:
            packet = json.loads(data.decode('utf-8'))
            header = packet.get("header", {})
            if header.get("room_id") != self.room_id:
                return
            ptype = header.get("type")
            handler = self._message_handlers.get(ptype)
            if handler:
                await handler(packet, addr)
            else:
                if ptype == "STATE" and hasattr(self.client, "game_ui"):
                    await self.client.game_ui.update_game_state(packet.get("payload", {}))
        except Exception as e:
            print(f"❌ Lỗi handle multicast packet: {e}")

    def register_handler(self, packet_type: str, handler: Callable):
        self._message_handlers[packet_type] = handler

    async def cleanup(self):
        self.running = False
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        self._receive_task = None

        if self.udp_socket:
            try:
                if self.group_ip:
                    mreq = struct.pack("4sL", socket.inet_aton(self.group_ip), socket.INADDR_ANY)
                    self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
                self.udp_socket.close()
            except Exception as e:
                print(f"⚠️ Lỗi close multicast socket: {e}")
            finally:
                self.udp_socket = None
        self.group_ip = None
        self.port = None
        self.room_id = None
        self._message_handlers.clear()

    async def leave_multicast_group(self):
        await self.cleanup()

    def is_connected(self) -> bool:
        return self.running and self.udp_socket is not None
