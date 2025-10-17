import asyncio
from .network.multicast_manager import MonopolyMulticastClient


async def main():
    client = MonopolyMulticastClient()
    await client.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")