"""
main.py

🎯 Entry point cho Monopoly UDP Multicast Server (phiên bản sử dụng network_utils)
- Khởi tạo logger, cấu hình, và các module phụ trợ
- Load danh sách phòng từ RoomManager
- Khởi tạo TCP Command Server (client gửi lệnh)
- Lắng nghe UDP Multicast Group cho event/state
- Giám sát vòng đời phòng và event loop chính
"""

import asyncio
import signal
import sys
import time
from utils import logger
from rooms.room_manager import RoomManager
from game.game_manager import GameManager
from network.network_utils import (
    create_tcp_server,
    create_udp_socket,
    join_multicast_group,
    send_udp,
    receive,
)

# ============================================================
# GLOBAL CONFIGURATION
# ============================================================

SERVER_CONFIG = {
    "tcp_host": "0.0.0.0",
    "tcp_port": 5050,
    "udp_ttl": 2,
    "tick_rate": 1.0,  # giây / vòng loop chính
}

running = True
room_manager: RoomManager = None


# ============================================================
# Initialization
# ============================================================

def initialize_system():
    """
    ✅ Khởi tạo hệ thống server:
     - RoomManager
     - TCP server
     - UDP sockets (cho multicast)
    """
    global room_manager
    logger.info("🚀 Initializing Monopoly Server (NetworkUtils edition)...")

    # 1️⃣ Khởi tạo Room Manager
    room_manager = RoomManager()

    # 2️⃣ Tạo sẵn vài phòng mẫu
    for i in range(1, 3):
        room_manager.create_room(f"ROOM_{i:02d}")

    logger.info(f"✅ {len(room_manager.rooms)} rooms initialized.")


# ============================================================
# TCP SERVER HANDLER
# ============================================================

async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Xử lý kết nối TCP từ client."""
    addr = writer.get_extra_info("peername")
    logger.info(f"🔌 New TCP connection from {addr}")

    try:
        while running:
            data = await receive(reader, protocol="tcp")
            if not data:
                logger.info(f"❌ Client {addr} disconnected.")
                break

            cmd = data.get("cmd")
            payload = data.get("data", {})

            if cmd == "LIST_ROOMS":
                rooms = room_manager.list_rooms()
                await send({"cmd": "ROOM_LIST", "data": rooms}, writer, protocol="tcp")

            elif cmd == "CREATE_ROOM":
                room_id = payload.get("room_id")
                info = room_manager.create_room(room_id)
                await send({"cmd": "ROOM_CREATED", "data": info}, writer, protocol="tcp")

            else:
                await send({"error": f"Unknown command: {cmd}"}, writer, protocol="tcp")

    except Exception as e:
        logger.error(f"[TCP ERROR] {e}")
    finally:
        writer.close()
        await writer.wait_closed()


# ============================================================
# UDP MULTICAST LISTENER
# ============================================================

async def udp_multicast_listener(udp_sock):
    """Lắng nghe các gói multicast UDP từ các phòng."""
    logger.info("📡 UDP Multicast listener started.")
    while running:
        try:
            data, addr = await receive(udp_sock, protocol="udp")
            logger.debug(f"[MULTICAST] From {addr}: {data}")
        except Exception as e:
            logger.error(f"[UDP ERROR] {e}")
            await asyncio.sleep(0.1)


# ============================================================
# MAIN LOOP
# ============================================================

async def main_loop(udp_sock):
    """
    🧠 Vòng lặp chính của server:
      - Gửi trạng thái phòng định kỳ
      - Theo dõi heartbeat
    """
    global running
    tick = SERVER_CONFIG["tick_rate"]

    logger.info("🌀 Main loop started.")
    while running:
        for room_id, room in list(room_manager.rooms.items()):
            ip = room["group_ip"]
            port = room["port"]
            state = {
                "room": room_id,
                "players": room["players"],
                "tick": time.time()
            }
            await send_udp(udp_sock, state, ip, port)
            logger.debug(f"📤 State update sent to {room_id} ({ip}:{port})")

        await asyncio.sleep(tick)
    logger.info("🧩 Main loop stopped.")


# ============================================================
# SIGNAL HANDLING
# ============================================================

def signal_handler(sig, frame):
    global running
    logger.warning("⚠️ Signal received, shutting down server...")
    running = False


# ============================================================
# ENTRY POINT
# ============================================================

async def run_server():
    """Khởi động toàn bộ server."""
    global running

    signal.signal(signal.SIGINT, signal_handler)
    initialize_system()

    # 1️⃣ Khởi tạo TCP server
    tcp_server = await create_tcp_server(
        host=SERVER_CONFIG["tcp_host"],
        port=SERVER_CONFIG["tcp_port"],
        handler=handle_tcp_client
    )

    # 2️⃣ Khởi tạo UDP socket cho multicast
    udp_sock = create_udp_socket(multicast=True)

    # Join toàn bộ group trong danh sách phòng
    for room in room_manager.rooms.values():
        join_multicast_group(udp_sock, room["group_ip"])
        logger.info(f"🧩 Joined multicast group {room['group_ip']}:{room['port']}")

    # 3️⃣ Tạo task song song
    tasks = [
        asyncio.create_task(udp_multicast_listener(udp_sock)),
        asyncio.create_task(main_loop(udp_sock))
    ]

    logger.info("🌐 Monopoly Server running. Press Ctrl+C to stop.")
    await asyncio.gather(*tasks)

    tcp_server.close()
    await tcp_server.wait_closed()
    udp_sock.close()
    logger.info("✅ Server stopped cleanly.")


if __name__ == "__main__":
    asyncio.run(run_server())
