import asyncio
from ..client.network.client import MonopolyClient

async def main():
    client = MonopolyClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
