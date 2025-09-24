import asyncio
from server.network import ChatServer

if __name__ == "__main__":
    server = ChatServer()
    asyncio.run(server.run())

