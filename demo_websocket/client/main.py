import asyncio
from client.network import ChatClient

if __name__ == "__main__":
    client = ChatClient()
    asyncio.run(client.run())
