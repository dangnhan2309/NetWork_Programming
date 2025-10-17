# src/client/main.py
import asyncio
import sys
import os

from .core.game_client import MonopolyGameClient
from .network.tcp_client import TCPClient
from .network.multicast_client import MulticastClient

async def main():
    """Hàm main chạy client"""
    print("🎮 MONOPOLY MULTICAST CLIENT")
    print("=" * 40)
    
    # Khởi tạo client
    client = MonopolyGameClient(
        server_host='localhost', 
        server_port=5050
    )
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Đã thoát game!")
    except Exception as e:
        print(f"💥 Lỗi không mong muốn: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    # Kiểm tra Python version
    if sys.version_info < (3, 7):
        print("❌ Yêu cầu Python 3.7+")
        sys.exit(1)
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Đã thoát game!")