# import socket
# import struct
# import threading
# from ..utils import logger
# from ..utils import packet_format as PacketFormat
# from .multiplecast_manager import MulticastManager
# from .network_utils import udp_send, udp_receive
#
#
# class UDPMulticast:
#     """
#     Quản lý UDP multicast cho việc gửi/nhận sự kiện game trong phòng.
#     Dùng cho các hành động như “ROLL_RESULT”, “BOARD_UPDATE”.
#     """
#
#     def __init__(self, room_id: str, is_server: bool = False):
#         self.room_id = room_id
#         self.is_server = is_server
#         self.manager = MulticastManager()
#         self.group_info = self.manager.create_group(room_id)
#         self.ip = self.group_info["ip"]
#         self.port = self.group_info["port"]
#         self.sock = None
#         self.running = False
#
#     # --------------------------------------------------------------------------
#     def _create_socket(self):
#         """Khởi tạo socket UDP multicast"""
#         try:
#             sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#             sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#             sock.bind(('', self.port))
#             mreq = struct.pack("4sl", socket.inet_aton(self.ip), socket.INADDR_ANY)
#             sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
#             sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
#             self.sock = sock
#             logger.info(f"[UDP] Joined multicast group {self.ip}:{self.port} (Room={self.room_id})")
#         except OSError as e:
#             logger.warning(f"[UDP FALLBACK] Cannot join multicast, fallback to unicast mode: {e}")
#             self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
#     # --------------------------------------------------------------------------
#     def start_listener(self, handler_func):
#         """
#         Bắt đầu thread lắng nghe packet multicast hoặc UDP fallback.
#         :param handler_func: callback(packet_dict)
#         """
#         if self.sock is None:
#             self._create_socket()
#
#         self.running = True
#
#         def listen_loop():
#             while self.running:
#                 packet = udp_receive(self.sock)
#                 if packet:
#                     handler_func(packet)
#
#         threading.Thread(target=listen_loop, daemon=True).start()
#         logger.info(f"[UDP] Listener started for room {self.room_id}")
#
#     # --------------------------------------------------------------------------
#     def send_packet(self, packet: dict):
#         """
#         Gửi packet multicast (hoặc fallback nếu cần).
#         :param packet: dict (định dạng chuẩn theo PacketFormat)
#         """
#         if self.sock is None:
#             self._create_socket()
#
#         try:
#             udp_send(self.sock, (self.ip, self.port), packet)
#             logger.debug(f"[UDP] Sent packet to {self.ip}:{self.port}")
#         except Exception as e:
#             logger.error(f"[UDP SEND ERROR] {e}")
#
#     # --------------------------------------------------------------------------
#     def send_event(self, sender, action, payload=None, target="ALL"):
#         """
#         Gửi event game, ví dụ: ROLL_RESULT, BOARD_UPDATE
#         """
#         packet = PacketFormat.build_event_packet(
#             room_id=self.room_id,
#             sender=sender,
#             target=target,
#             action=action,
#             payload=payload or {}
#         )
#         self.send_packet(packet)
#
#     # --------------------------------------------------------------------------
#     def send_command(self, sender, action, args=None, payload=None, target="SERVER"):
#         """
#         Gửi lệnh từ client hoặc server (ROLL, BUY, BUILD, ...)
#         """
#         packet = PacketFormat.build_command_packet(
#             room_id=self.room_id,
#             sender=sender,
#             target=target,
#             action=action,
#             args=args or {},
#             payload=payload or {}
#         )
#         self.send_packet(packet)
#
#     # --------------------------------------------------------------------------
#     def stop(self):
#         """Dừng listener và rời nhóm multicast"""
#         self.running = False
#         if self.sock:
#             try:
#                 mreq = struct.pack("4sl", socket.inet_aton(self.ip), socket.INADDR_ANY)
#                 self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
#             except OSError:
#                 pass
#             self.sock.close()
#             logger.info(f"[UDP] Left multicast group {self.ip}:{self.port}")
#         self.manager.remove_group(self.room_id)
#
#
# # --------------------------------------------------------------------------
# if __name__ == "__main__":
#     """Test multicast và fallback (chạy cả server + client trên cùng máy)."""
#     import time
#
#     def on_receive(packet):
#         logger.info(f"[RECEIVED] {packet['header']['sender']} → {packet['command']['action']}")
#
#     server = UDPMulticast(room_id="ROOM_01", is_server=True)
#     client = UDPMulticast(room_id="ROOM_01", is_server=False)
#
#     server.start_listener(on_receive)
#     client.start_listener(on_receive)
#
#     # Client gửi lệnh ROLL
#     client.send_command(sender="Alice", action="ROLL", payload={"message": "Rolling dice..."})
#     time.sleep(1)
#
#     # Server gửi kết quả xúc xắc
#     server.send_event(
#         sender="SERVER",
#         action="ROLL_RESULT",
#         payload={"player": "Alice", "dice": [4, 2], "new_position": 18}
#     )
#
#     # Server gửi cập nhật bàn cờ
#     server.send_event(
#         sender="SERVER",
#         action="BOARD_UPDATE",
#         payload={"tile": "Park Place", "owner": "Alice"}
#     )
#
#     time.sleep(2)
#     server.stop()
#     client.stop()
