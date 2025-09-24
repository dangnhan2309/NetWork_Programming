import asyncio
from client.network import ChatClient

if __name__ == "__main__":
    client = ChatClient(uri="ws://192.168.10.23:8765",name="Nhân")
    asyncio.run(client.run())
