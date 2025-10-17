# import json
# import asyncio
# import signal
# import time
# import socket
# from datetime import datetime
#
# # Import các module cần thiết
# from .utils.logger import Logger
# #from .utils.packet_format import PacketFormat
# from .rooms.room_manager import RoomManager
#
# # ============================================================
# # GLOBAL CONFIGURATION
# # ============================================================
#
# SERVER_CONFIG = {
#     "tcp_host": "0.0.0.0",
#     "tcp_port": 5050,
#     "udp_ttl": 2,
#     "tick_rate": 5.0,
# }
#
# running = True
#
# # ============================================================
# # Initialization
# # ============================================================
#
# logger = Logger("Server")
#
# async def initialize_system():
#     """
#     ✅ Khởi tạo hệ thống server
#     """
#     global room_manager
#     logger.info("🚀 Initializing Monopoly Server...")
#
#     # 1️⃣ Khởi tạo Room Manager
#     room_manager = RoomManager(logger)
#
#     # 2️⃣ Tạo sẵn vài phòng mẫu
#
#
#     logger.info(f"✅ {len(room_manager.rooms)} rooms initialized.")
#
# # ============================================================
# # TCP SERVER HANDLER - ĐÃ SỬA LỖI JSON SERIALIZE
# # ============================================================
#
# async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
#     """Xử lý kết nối TCP từ client - ĐÃ SỬA LỖI JSON"""
#     addr = writer.get_extra_info("peername")
#     logger.info(f"🔌 New TCP connection from {addr}")
#
#     client_buffer = ""
#
#     try:
#         while running:
#             try:
#                 # Đọc dữ liệu với timeout
#                 data = await asyncio.wait_for(reader.read(1024), timeout=30.0)
#
#                 if not data:
#                     logger.info(f"🔌 Client {addr} disconnected (no data)")
#                     break
#
#                 # Decode và thêm vào buffer
#                 chunk = data.decode('utf-8')
#                 client_buffer += chunk
#                 logger.debug(f"📨 Received {len(data)} bytes from {addr}, buffer: {len(client_buffer)} chars")
#
#                 # Xử lý tất cả các message hoàn chỉnh trong buffer
#                 while client_buffer:
#                     if '\n' in client_buffer:
#                         message_end = client_buffer.find('\n')
#                         message_str = client_buffer[:message_end]
#                         client_buffer = client_buffer[message_end + 1:]
#
#                         if message_str.strip():
#                             await process_single_message(message_str, addr, writer)
#                     else:
#                         break
#
#             except asyncio.TimeoutError:
#                 continue
#             except ConnectionResetError:
#                 logger.info(f"🔌 Client {addr} disconnected forcibly")
#                 break
#             except Exception as e:
#                 logger.error(f"❌ Error handling client {addr}: {e}")
#                 break
#
#     except Exception as e:
#         logger.error(f"❌ TCP handler error for {addr}: {e}")
#     finally:
#         try:
#             writer.close()
#             await writer.wait_closed()
#             logger.info(f"🔌 Client {addr} fully disconnected")
#         except:
#             pass
#
# async def process_single_message(message_str: str, addr: tuple, writer: asyncio.StreamWriter):
#     """Xử lý một message JSON hoàn chỉnh - ĐÃ SỬA HOÀN TOÀN"""
#     try:
#         # Parse JSON
#         data = json.loads(message_str)
#         logger.info(f"📨 Received from {addr}: {data.get('cmd', 'UNKNOWN')}")
#
#         cmd = data.get("cmd")
#         payload = data.get("data", {})
#
#         # Xử lý commands
#         if cmd == "LIST_ROOMS":
#             rooms = await room_manager.list_rooms()
#             response = {"cmd": "ROOM_LIST", "data": rooms, "status": "OK"}
#
#         # Trong process_single_message, thêm debug:
#         elif cmd == "CREATE_ROOM":
#             room_id = payload.get("room_id", f"ROOM_{int(time.time())}")
#             room_info = await room_manager.create_room(room_id)
#
#             logger.debug(f"🔍 Room info type: {type(room_info)}")
#             logger.debug(f"🔍 Room info keys: {room_info.keys() if room_info else 'None'}")
#
#             if room_info:
#                 # Thử serialize để test
#                 try:
#                     test_json = json.dumps(room_info)
#                     logger.debug("✅ Room info is JSON serializable")
#                 except Exception as e:
#                     logger.error(f"❌ Room info NOT serializable: {e}")
#
#                 response = {
#                     "cmd": "ROOM_CREATED",
#                     "data": room_info,
#                     "status": "OK"
#                 }
#
#         elif cmd == "JOIN_ROOM":
#             room_id = payload.get("room_id")
#             player_name = payload.get("player_name", f"Player_{addr[1]}")
#
#             if room_id and room_id in room_manager.rooms:
#                 room_info = await room_manager.add_player(room_id, player_name)  # Đã trả về serializable
#
#                 if room_info:
#                     response = {
#                         "cmd": "JOIN_SUCCESS",
#                         "status": "OK",
#                         "data": room_info  # Đã là serializable
#                     }
#                     logger.info(f"✅ Player {player_name} joined {room_id}")
#                 else:
#                     response = {"cmd": "ERROR", "status": "ERROR", "message": "Join room failed"}
#             else:
#                 rooms = await room_manager.list_rooms()
#                 available_rooms = list(rooms.keys())
#                 response = {
#                     "cmd": "ERROR",
#                     "status": "ERROR",
#                     "message": f"Room '{room_id}' not found. Available: {', '.join(available_rooms)}"
#                 }
#
#         elif cmd == "LEAVE_ROOM":
#             room_id = payload.get("room_id")
#             player_name = payload.get("player_name")
#             if room_id and player_name:
#                 success = await room_manager.remove_player(room_id, player_name)
#                 response = {"cmd": "LEAVE_RESULT", "status": "OK" if success else "ERROR"}
#             else:
#                 response = {"cmd": "ERROR", "status": "ERROR", "message": "Missing room_id or player_name"}
#
#         else:
#             response = {"cmd": "ERROR", "status": "ERROR", "message": f"Unknown command: {cmd}"}
#
#         # Gửi phản hồi - ĐẢM BẢO response có thể serialize
#         response_str = json.dumps(response, ensure_ascii=False) + "\n"
#         writer.write(response_str.encode('utf-8'))
#         await writer.drain()
#         logger.debug(f"📤 Sent response to {addr}: {response.get('cmd')}")
#
#     except json.JSONDecodeError as e:
#         logger.error(f"❌ JSON decode error from {addr}: {e}")
#         error_response = {"cmd": "ERROR", "status": "ERROR", "message": "Invalid JSON format"}
#         writer.write((json.dumps(error_response) + "\n").encode('utf-8'))
#         await writer.drain()
#     except Exception as e:
#         logger.error(f"❌ Error processing message from {addr}: {e}")
#         error_response = {"cmd": "ERROR", "status": "ERROR", "message": "Internal server error"}
#         writer.write((json.dumps(error_response) + "\n").encode('utf-8'))
#         await writer.drain()
#
# # ============================================================
# # UDP MULTICAST LISTENER
# # ============================================================
#
# async def udp_multicast_listener():
#     """Lắng nghe các gói multicast UDP từ các phòng"""
#     logger.info("📡 UDP Multicast listener started.")
#
#     try:
#         udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         udp_sock.bind(('', 0))
#         udp_sock.setblocking(False)
#
#         loop = asyncio.get_event_loop()
#
#         while running:
#             try:
#                 data, addr = await loop.sock_recvfrom(udp_sock, 4096)
#                 if data:
#                     try:
#                         packet = json.loads(data.decode('utf-8'))
#                         room_id = packet.get('header', {}).get('room_id')
#                         action = packet.get('command', {}).get('action', 'UNKNOWN')
#                         if room_id:
#                             logger.debug(f"[MULTICAST] Room {room_id} - {action} from {addr}")
#                     except json.JSONDecodeError:
#                         logger.warning(f"[MULTICAST] Invalid JSON from {addr}")
#             except BlockingIOError:
#                 await asyncio.sleep(0.1)
#             except Exception as e:
#                 if running:
#                     logger.error(f"[UDP LISTENER ERROR] {e}")
#                     await asyncio.sleep(1)
#
#     except Exception as e:
#         logger.error(f"[UDP LISTENER FATAL] {e}")
#     finally:
#         if 'udp_sock' in locals():
#             udp_sock.close()
#
# # ============================================================
# # MAIN SERVER FUNCTIONS
# # ============================================================
#
# async def shutdown():
#     """Dọn dẹp tài nguyên khi tắt server"""
#     global running
#     running = False
#     logger.info("🛑 Shutting down server...")
#
#     # Đóng tất cả room sockets
#     if room_manager:
#         for room_id, room_info in room_manager.rooms.items():
#             sock = room_info.get("socket")
#             if sock:
#                 try:
#                     sock.close()
#                     logger.debug(f"🔌 Closed socket for room {room_id}")
#                 except Exception as e:
#                     logger.error(f"❌ Error closing socket for {room_id}: {e}")
#
#     await asyncio.sleep(1)
#     logger.info("✅ Server shutdown complete")
#
# def signal_handler(sig, frame):
#     """Xử lý signal để shutdown graceful"""
#     global running
#     logger.warning("⚠️ Signal received, shutting down server...")
#     running = False
#
# async def main_loop():
#     """Vòng lặp chính của server - Sử dụng internal room info"""
#     global running
#
#     logger.info("🌀 Main loop started.")
#
#     while running:
#         try:
#             # Lấy internal room info (có socket) cho heartbeat
#             for room_id, room_info in room_manager.rooms.items():  # Dùng trực tiếp internal storage
#                 try:
#                     # Tạo heartbeat packet
#                     state_packet = {
#                         "header": {
#                             "packet_id": f"heartbeat-{int(time.time())}",
#                             "room_id": room_id,
#                             "sender": "SERVER",
#                             "target": "ALL",
#                             "type": "STATE",
#                             "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
#                             "version": "1.0"
#                         },
#                         "meta": {
#                             "seq_id": int(time.time() * 1000),
#                             "ack": False,
#                             "reliable": False,
#                             "hop_count": 1
#                         },
#                         "command": {
#                             "action": "HEARTBEAT",
#                             "args": {}
#                         },
#                         "payload": {
#                             "room_id": room_id,
#                             "players": room_info["players"],
#                             "timestamp": time.time(),
#                             "type": "HEARTBEAT",
#                             "active_rooms": len(room_manager.rooms)
#                         }
#                     }
#
#                     # Gửi qua UDP multicast - dùng socket từ internal storage
#                     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
#                         sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
#                         sock.sendto(
#                             json.dumps(state_packet).encode('utf-8'),
#                             (room_info["multicast_ip"], room_info["port"])
#                         )
#
#                     logger.debug(f"📤 Heartbeat sent to {room_id}")
#                 except Exception as e:
#                     logger.error(f"❌ Error sending heartbeat to {room_id}: {e}")
#
#             await asyncio.sleep(SERVER_CONFIG["tick_rate"])
#
#         except Exception as e:
#             logger.error(f"❌ Main loop error: {e}")
#             await asyncio.sleep(1)
#
#     logger.info("🧩 Main loop stopped.")
#
# async def run_server():
#     """Khởi động toàn bộ server"""
#     global running
#
#     signal.signal(signal.SIGINT, signal_handler)
#     signal.signal(signal.SIGTERM, signal_handler)
#
#     await initialize_system()
#
#     try:
#         # 1️⃣ Khởi tạo TCP server
#         logger.info(f"🔄 Starting TCP server on {SERVER_CONFIG['tcp_host']}:{SERVER_CONFIG['tcp_port']}")
#         tcp_server = await asyncio.start_server(
#             handle_tcp_client,
#             SERVER_CONFIG["tcp_host"],
#             SERVER_CONFIG["tcp_port"]
#         )
#
#         # 2️⃣ Tạo các task chạy song song
#         udp_task = asyncio.create_task(udp_multicast_listener())
#         main_loop_task = asyncio.create_task(main_loop())
#
#         logger.info("🌐 Monopoly Server is NOW RUNNING!")
#         logger.info(f"   TCP: {SERVER_CONFIG['tcp_host']}:{SERVER_CONFIG['tcp_port']}")
#         logger.info(f"   Rooms: {len(room_manager.rooms)}")
#         logger.info("   Press Ctrl+C to stop")
#
#         async with tcp_server:
#             await tcp_server.serve_forever()
#
#     except asyncio.CancelledError:
#         logger.info("Server stopped by user")
#     except Exception as e:
#         logger.error(f"❌ Server startup failed: {e}")
#         raise
#     finally:
#         for task in [udp_task, main_loop_task]:
#             if task and not task.done():
#                 task.cancel()
#                 try:
#                     await task
#                 except asyncio.CancelledError:
#                     pass
#
#         await shutdown()
#
# if __name__ == "__main__":
#     print("🚀 Starting Monopoly Server...")
#     print("   Make sure the client uses the same host and port")
#     print("   Default: localhost:5050")
#
#     try:
#         asyncio.run(run_server())
#     except KeyboardInterrupt:
#         print("👋 Server stopped by user")
#     except Exception as e:
#         print(f"💥 Server crashed: {e}")
#------------------------------------------------------------------------------------
import json
import asyncio
import signal
import time
from datetime import datetime
from typing import Optional

# Import các module cần thiết
from .utils.logger import Logger
from .rooms.room_manager import RoomManager
from .network.network_manager import NetworkManager  # <-- Đã thêm NetworkManager

# ============================================================
# GLOBAL CONFIGURATION
# ============================================================

SERVER_CONFIG = {
    "tcp_host": "0.0.0.0",
    "tcp_port": 5050,
    "udp_ttl": 2,
    "tick_rate": 5.0,
}

running = True
# Khai báo các biến global cần thiết
room_manager: Optional[RoomManager] = None
network_manager: Optional[NetworkManager] = None
logger = Logger("Server")


# ============================================================
# Initialization
# ============================================================

async def initialize_system():
    """
    ✅ Khởi tạo hệ thống server: Khởi tạo NetworkManager trước RoomManager.
    """
    global room_manager
    global network_manager
    logger.info("🚀 Initializing Monopoly Server...")

    # 0️⃣ Khởi tạo Network Manager (Bao gồm MulticastManager)
    # Giả định NetworkManager nhận logger trong __init__
    network_manager = NetworkManager(logger_ins=logger)

    # 1️⃣ Khởi tạo Room Manager
    # RoomManager cần NetworkManager để tạo group multicast cho phòng
    room_manager = RoomManager(networkmanager=network_manager, logger=logger)

    # 2️⃣ Tạo sẵn vài phòng mẫu
    await room_manager.create_room("ROOM_01", host_id=None)
    await room_manager.create_room("ROOM_02", host_id=None)

    logger.info(f"✅ {len(room_manager.rooms)} rooms initialized.")


# ============================================================
# TCP SERVER HANDLER
# ============================================================

async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Xử lý kết nối TCP từ client"""
    addr = writer.get_extra_info("peername")
    logger.info(f"🔌 New TCP connection from {addr}")

    client_buffer = ""

    try:
        while running:
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=30.0)

                if not data:
                    logger.info(f"🔌 Client {addr} disconnected (no data)")
                    break

                chunk = data.decode('utf-8')
                client_buffer += chunk

                # Xử lý tất cả các message hoàn chỉnh trong buffer
                while client_buffer:
                    if '\n' in client_buffer:
                        message_end = client_buffer.find('\n')
                        message_str = client_buffer[:message_end]
                        client_buffer = client_buffer[message_end + 1:]

                        if message_str.strip():
                            # Truyền writer để có thể gửi phản hồi trực tiếp qua TCP
                            await process_single_message(message_str, addr, writer)
                    else:
                        break

            except asyncio.TimeoutError:
                continue
            except ConnectionResetError:
                logger.info(f"🔌 Client {addr} disconnected forcibly")
                break
            except Exception as ee:
                # Vẫn giữ khối này để bắt các lỗi logic hoặc socket hiếm
                logger.error(f"❌ Error handling client {addr}: {ee}")
                break

    finally:
        try:
            writer.close()
            await writer.wait_closed()
            logger.info(f"🔌 Client {addr} fully disconnected")
            # TƯƠNG LAI: Gọi network_manager.remove_client(client_id)
        except:
            pass


async def process_single_message(message_str: str, addr: tuple, writer: asyncio.StreamWriter):
    """Xử lý một message JSON hoàn chỉnh"""
    response = {"cmd": "ERROR", "status": "ERROR", "message": "Internal server error"}

    try:
        # Parse JSON
        data = json.loads(message_str)
        cmd = data.get("cmd")
        payload = data.get("data", {})

        logger.info(f"📨 Received from {addr}: {cmd}")

        # Xử lý commands
        if cmd == "LIST_ROOMS":
            rooms = await room_manager.list_rooms()
            response = {"cmd": "ROOM_LIST", "data": rooms, "status": "OK"}

        elif cmd == "CREATE_ROOM":
            room_id = payload.get("room_id", f"ROOM_{int(time.time())}")
            # host_id được giả định là None hoặc lấy từ payload
            room_info = await room_manager.create_room(room_id, host_id=None)
            response = {"cmd": "ROOM_CREATED", "data": room_info, "status": "OK"} if room_info else response

        elif cmd == "JOIN_ROOM":
            room_id = payload.get("room_id")
            player_name = payload.get("player_name", f"Player_{addr[1]}")

            # Giả định client_id (định danh duy nhất) được tạo ra từ đâu đó
            client_id = f"{addr[0]}:{addr[1]}"

            if room_id and room_id in room_manager.rooms:
                room_info = await room_manager.add_player(room_id, player_name, client_id)
                if room_info:
                    response = {"cmd": "JOIN_SUCCESS", "status": "OK", "data": room_info}
                    # TƯƠNG LAI: network_manager.map_client_to_room(client_id, room_id)
                else:
                    response = {"cmd": "ERROR", "status": "ERROR", "message": "Join room failed (Room full/In game)"}
            else:
                response = {"cmd": "ERROR", "status": "ERROR", "message": f"Room '{room_id}' not found."}

        elif cmd == "LEAVE_ROOM":
            room_id = payload.get("room_id")
            player_id = payload.get("player_id")  # Giả định client gửi player_id/name

            if room_id and player_id:
                success = await room_manager.remove_player(room_id, player_id)
                response = {"cmd": "LEAVE_RESULT", "status": "OK" if success else "ERROR"}
            else:
                response = {"cmd": "ERROR", "status": "ERROR", "message": "Missing room_id or player_id"}

        else:
            response = {"cmd": "ERROR", "status": "ERROR", "message": f"Unknown command: {cmd}"}

    except json.JSONDecodeError as ee:
        logger.error(f"❌ JSON decode error from {addr}: {ee}")
        response = {"cmd": "ERROR", "status": "ERROR", "message": "Invalid JSON format"}
    except Exception as ee:
        logger.error(f"❌ Error processing message from {addr}: {ee}")
        # response đã là Internal server error ở đầu hàm

    finally:
        # Gửi phản hồi
        response_str = json.dumps(response, ensure_ascii=False) + "\n"
        writer.write(response_str.encode('utf-8'))
        await writer.drain()
        logger.debug(f"📤 Sent response: {response.get('cmd')} to {addr}")


# ============================================================
# MAIN SERVER FUNCTIONS
# ============================================================

async def shutdown():
    """Dọn dẹp tài nguyên khi tắt server"""
    global running
    global network_manager  # Đảm bảo network_manager được truy cập

    running = False
    logger.info("🛑 Shutting down server...")

    # 🔑 GỌI PHƯƠNG THỨC ĐÓNG SOCKET CHÍNH XÁC 🔑
    if network_manager:
        logger.info("📡 Closing multicast sockets...")
        # Gọi hàm đóng tất cả socket multicast
        network_manager.multicast.close_all_multicast_groups()

    # Giữ lại đoạn code kiểm tra RoomManager
    if room_manager:
        # Tương lai: bạn có thể gọi room_manager.cleanup_rooms() để xóa dữ liệu trạng thái
        pass

    await asyncio.sleep(1)
    logger.info("✅ Server shutdown complete")


def signal_handler(sig, frame):
    """Xử lý signal để shutdown graceful"""
    global running
    logger.warning("⚠️ Signal received, shutting down server...")
    running = False


async def main_loop():
    """Vòng lặp chính của server (Heartbeat/Game Tick)"""
    global running

    logger.info("🌀 Main loop started.")

    while running:
        try:
            # Gửi Heartbeat cho TẤT CẢ các phòng
            for room_id, room_info in room_manager.rooms.items():
                try:
                    # 1. Tạo Heartbeat Packet
                    state_packet = {
                        "header": {
                            "room_id": room_id,
                            "type": "STATE",
                            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        },
                        "command": {"action": "HEARTBEAT"},
                        "payload": {
                            "players": [p.to_dict() for p in room_info["state"].players],
                            # Giả định RoomState có thuộc tính players
                            "active_rooms": len(room_manager.rooms)
                        }
                    }

                    # 2. 📤 Gửi qua NetworkManager 📤
                    # NetworkManager sẽ tìm IP/Port của phòng và gửi Multicast
                    network_manager.send_packet(room_id, state_packet)

                    logger.debug(f"📤 Heartbeat sent to {room_id}")
                except Exception as e:
                    logger.error(f"❌ Error sending heartbeat to {room_id}: {e}")

            await asyncio.sleep(SERVER_CONFIG["tick_rate"])

        except Exception as e:
            logger.error(f"❌ Main loop error: {e}")
            await asyncio.sleep(1)

    logger.info("🧩 Main loop stopped.")


async def run_server():
    """Khởi động toàn bộ server"""
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await initialize_system()

    try:
        # 1️⃣ Khởi tạo TCP server
        logger.info(f"🔄 Starting TCP server on {SERVER_CONFIG['tcp_host']}:{SERVER_CONFIG['tcp_port']}")
        tcp_server = await asyncio.start_server(
            handle_tcp_client,
            SERVER_CONFIG["tcp_host"],
            SERVER_CONFIG["tcp_port"]
        )

        # 2️⃣ Tạo các task chạy song song
        # Sử dụng listen_loop của NetworkManager thay vì hàm global
        udp_task = asyncio.create_task(network_manager.listen_loop())
        main_loop_task = asyncio.create_task(main_loop())

        logger.info("🌐 Monopoly Server is NOW RUNNING!")
        logger.info(f"   TCP: {SERVER_CONFIG['tcp_host']}:{SERVER_CONFIG['tcp_port']}")
        logger.info(f"   Rooms: {len(room_manager.rooms)}")
        logger.info("   Press Ctrl+C to stop")

        async with tcp_server:
            await tcp_server.serve_forever()

    except asyncio.CancelledError:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        raise
    finally:
        for task in [udp_task, main_loop_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.warning("👋 Server execution manually terminated.")
    except Exception as e:
        logger.error(message=f"💥 Server crashed unexpectedly during startup: {e}")