"""
Main server file cho Monopoly Multiplayer Game
"""

import asyncio
from src.server.network import MonopolyServer 

async def main():
    server = MonopolyServer(host="localhost", port=8765)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())