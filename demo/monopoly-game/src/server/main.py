"""
Server Main Entry Point
"""
import asyncio
import sys
from .network import ServerNetwork

async def main():
    server = ServerNetwork(host='0.0.0.0', port=12345)

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        await server.stop()
        print("✅ Server stopped successfully")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server terminated by user")