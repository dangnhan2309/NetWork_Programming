# import socket
# import threading
# from ..utils import logger
# from ..utils import packet_format as PacketFormat
# from ..network import network_utils as net
#
# class TCPHandler:
#     """
#     TCP server cho việc nhận/gửi lệnh điều khiển đáng tin cậy (join room, exit, system command).
#     Hoạt động song song với multicast UDP trong game.
#     """
#
#     def __init__(self, host='0.0.0.0', port=5050):
#         self.host = host
#         self.port = port
#         self.server_socket = None
#         self.running = False
#         self.client_threads = []
#         self.clients = {}  # {addr: {'socket': sock, 'player': name, 'room_id': room}}
#         logger.info(f"[TCP] Initialized at {host}:{port}")
#
#     # --------------------------------------------------------------------------
#     def start(self, on_command_callback):
#         """
#         Bắt đầu TCP server.
#         :param on_command_callback: function(packet, addr) — được gọi mỗi khi nhận gói hợp lệ
#         """
#         self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.server_socket.bind((self.host, self.port))
#         self.server_socket.listen(10)
#         self.running = True
#
#         logger.info(f"[TCP] Listening on {self.host}:{self.port}")
#
#         def accept_loop():
#             while self.running:
#                 try:
#                     conn, addr = self.server_socket.accept()
#                     logger.info(f"[TCP] New connection from {addr}")
#                     self.clients[addr] = {"socket": conn, "player": None, "room_id": None}
#                     thread = threading.Thread(target=self._client_thread, args=(conn, addr, on_command_callback))
#                     thread.start()
#                     self.client_threads.append(thread)
#                 except Exception as e:
#                     logger.error(f"[TCP ACCEPT ERROR] {e}")
#
#         threading.Thread(target=accept_loop, daemon=True).start()
#
#     # --------------------------------------------------------------------------
#     def _client_thread(self, conn, addr, callback):
#         """Lắng nghe lệnh từ client TCP (sử dụng network_utils)."""
#         try:
#             with conn:
#                 while self.running:
#                     packet = net.tcp_receive(conn)
#                     if not packet:
#                         break
#
#                     logger.debug(f"[TCP] Received from {addr}: {packet.get('command', {}).get('action', 'UNKNOWN')}")
#                     callback(packet, addr)
#
#         except ConnectionResetError:
#             logger.warning(f"[TCP] Client disconnected abruptly: {addr}")
#         finally:
#             logger.info(f"[TCP] Connection closed: {addr}")
#             self.clients.pop(addr, None)
#
#     # --------------------------------------------------------------------------
#     def send_response(self, conn, packet: dict):
#         """Gửi phản hồi TCP cho client (qua network_utils)."""
#         try:
#             net.tcp_send(conn, packet)
#             logger.debug(f"[TCP] Sent response to client.")
#         except Exception as e:
#             logger.error(f"[TCP SEND ERROR] {e}")
#
#     # --------------------------------------------------------------------------
#     def broadcast_system_message(self, message: str):
#         """Gửi thông báo hệ thống đến tất cả client TCP."""
#         packet = PacketFormat.build_event_packet(
#             room_id="SYSTEM",
#             sender="SERVER",
#             target="ALL",
#             action="SYSTEM_MESSAGE",
#             payload={"message": message}
#         )
#
#         for addr, info in list(self.clients.items()):
#             sock = info["socket"]
#             try:
#                 net.tcp_send(sock, packet)
#             except Exception as e:
#                 logger.error(f"[TCP BROADCAST ERROR] {addr}: {e}")
#
#     # --------------------------------------------------------------------------
#     def stop(self):
#         """Dừng toàn bộ TCP server."""
#         self.running = False
#         for addr, info in self.clients.items():
#             try:
#                 info["socket"].close()
#             except:
#                 pass
#         if self.server_socket:
#             self.server_socket.close()
#         logger.info("[TCP] Server stopped.")
#
#
# # --------------------------------------------------------------------------
# if __name__ == "__main__":
#     """Demo test cho TCPHandler (client gửi command /join Alice)."""
#
#     def handle_packet(packet, addr):
#         logger.info(f"[COMMAND RECEIVED] From {addr}: {packet['command']['action']}")
#         if packet['command']['action'] == "JOIN":
#             player = packet['header']['sender']
#             room = packet['header']['room_id']
#             reply = PacketFormat.build_event_packet(
#                 room_id=room,
#                 sender="SERVER",
#                 target=player,
#                 action="JOIN_ACK",
#                 payload={"status": "OK", "message": f"{player} joined {room}"}
#             )
#             conn = tcp_server.clients[addr]["socket"]
#             tcp_server.send_response(conn, reply)
#
#     tcp_server = TCPHandler(host='127.0.0.1', port=5050)
#     tcp_server.start(handle_packet)
