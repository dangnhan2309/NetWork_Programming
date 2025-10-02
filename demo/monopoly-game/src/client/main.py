#!/usr/bin/env python3
"""
File chạy client Monopoly
"""

import asyncio
import sys
from .network import MonopolyClient


async def main():
    # Lấy địa chỉ server từ command line hoặc dùng mặc định
    server_host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    server_port = sys.argv[2] if len(sys.argv) > 2 else "8765"
    # -> nhận room ip tên
    uri = f"ws://{server_host}:{server_port}"
    
    print(f"🎮 Kết nối đến server: {uri}")
    
    client = MonopolyClient(uri)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    asyncio.run(main())