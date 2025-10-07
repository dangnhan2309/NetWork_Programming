#!/usr/bin/env python3
"""
Script khởi động server WebSocket
"""
import asyncio
import socket
from .network import ServerNetwork  # nếu file network.py ở cùng thư mục

def get_local_ip():
    """Lấy IP local của máy"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

async def main():
    local_ip = get_local_ip()

    print("🌐 MONOPOLY WEBSOCKET SERVER CONFIGURATION")
    print("="*50)
    print(f"📍 Local IP: {local_ip}")
    print(f"📍 Port: 12345")
    print(f"📍 Connect string: ws://{local_ip}:12345")
    print("="*50)
    print("⚠️  Đảm bảo firewall cho phép kết nối trên port 12345!")
    print("="*50)

    server = ServerNetwork(host='0.0.0.0', port=12345)

    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server terminated by user")
