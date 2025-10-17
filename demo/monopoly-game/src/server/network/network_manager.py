# server/network/network_manager.py
import asyncio
import json
from json import JSONDecodeError

from .multiplecast_manager import MulticastManager


class NetworkManager:
    """
    Bộ điều phối mạng hai chiều.
    - Gửi: gọi MulticastManager để điều hướng packet đến đúng phòng hoặc client.
    - Nhận: async listener cho multicast.
    - Quản lý: mapping client_id ↔ room_id.
    - Phát sự kiện: cho phép đăng ký callback (on_packet, on_join, on_leave, ...).
    """

    def __init__(self, logger_ins):
        self.client_room_map = {}      # {client_id: room_id}
        self.event_listeners = {}      # {"event_name": [callback_fn]}
        self._listening = False
        self.logger = logger_ins
        self.multicast = MulticastManager(logger_ins=self.logger)

    # ------------------------------------------------------------------
    # 🔌 CLIENT - ROOM MAPPING
    # ------------------------------------------------------------------
    def map_client_to_room(self, client_id: str, room_id: str):
        """Gán client vào room."""
        self.client_room_map[client_id] = room_id
        self.logger.debug(f"[NETWORK] Client {client_id} → Room {room_id}")

    def remove_client(self, client_id: str):
        """Xóa client khỏi mapping."""
        if client_id in self.client_room_map:
            del self.client_room_map[client_id]
            self.logger.debug(f"[NETWORK] Client {client_id} disconnected")

    # ------------------------------------------------------------------
    # 📨 SEND
    # ------------------------------------------------------------------
    def send_packet(self, room_id: str, packet: dict, target="all", role=None):
        """
        Gửi packet đến một phòng, một client hoặc theo vai trò.
        :param room_id: Mã phòng
        :param packet: Dữ liệu dạng dict
        :param target: "all" | client_id
        :param role: Nếu chỉ muốn gửi cho "host"/"observer"/"player"
        """
        group = self.multicast.groups.get(room_id)
        if not group:
            self.logger.warning(f"[NETWORK] Room '{room_id}' chưa có group multicast.")
            return

        try:
            self.multicast.send_packet(room_id, packet, target=target, role=role)
            if target == "all":
                self.logger.debug(f"[NETWORK SEND] Broadcast → Room {room_id}: {packet.get('type', '?')}")
            elif role:
                self.logger.debug(f"[NETWORK SEND] Role '{role}' → Room {room_id}: {packet.get('type', '?')}")
            else:
                self.logger.debug(f"[NETWORK SEND] To Client {target} in Room {room_id}: {packet.get('type', '?')}")
        except Exception as e:
            self.logger.error(f"[NETWORK SEND ERROR] {e}")

    def send_to_client(self, client_id: str, packet: dict):
        """Gửi packet đến client cụ thể."""
        room_id = self.client_room_map.get(client_id)
        if not room_id:
            self.logger.warning(f"[NETWORK] Client {client_id} không thuộc room nào.")
            return
        self.send_packet(room_id, packet, target=client_id)

    def broadcast_packet(self, packet: dict, role=None):
        """Phát packet toàn phòng (hoặc theo vai trò)."""
        room_id = packet.get("room_id")
        if not room_id:
            self.logger.error("[NETWORK] broadcast_packet: thiếu room_id trong packet.")
            return
        self.send_packet(room_id, packet, target="all", role=role)

    # ------------------------------------------------------------------
    # 📡 LISTEN LOOP (RECEIVE)
    # ------------------------------------------------------------------
    async def listen_loop(self):
        """Lắng nghe tất cả group multicast và phát sự kiện on_packet."""
        if self._listening:
            return
        self._listening = True
        loop = asyncio.get_event_loop()
        self.logger.info("[NETWORK] Listening for incoming packets...")

        while True:
            for room_id, group in list(self.multicast.groups.items()):
                sock = group["socket"]
                sock.setblocking(False)
                try:
                    data, addr = await loop.sock_recv(sock, 8192)
                    message = json.loads(data.decode("utf-8"))
                    message["room_id"] = room_id
                    message["addr"] = addr
                    await self.emit_event("on_packet", message)

                except OSError as e:
                    self.logger.debug(f"[NETWORK] Socket error in {room_id}: {e}")
                    continue
                except JSONDecodeError as e:
                    self.logger.error(f"[NETWORK] JSON decode error in {room_id} from {addr}: {e}")
                    continue
                except UnicodeDecodeError as e:
                    self.logger.error(f"[NETWORK] Decode error from {addr}: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"[NETWORK ERROR] Unexpected: {e}")
            await asyncio.sleep(0.01)

    # ------------------------------------------------------------------
    # ⚡ EVENT SYSTEM
    # ------------------------------------------------------------------
    def register_listener(self, event_name: str, callback):
        """Đăng ký callback khi có sự kiện mạng."""
        self.event_listeners.setdefault(event_name, []).append(callback)
        self.logger.debug(f"[NETWORK] Registered listener for '{event_name}'")

    async def emit_event(self, event_name: str, data):
        """Kích hoạt sự kiện và gọi tất cả callback."""
        listeners = self.event_listeners.get(event_name, [])
        for cb in listeners:
            try:
                await cb(data)
            except Exception as e:
                self.logger.error(f"[EVENT ERROR] {event_name}: {e}")
