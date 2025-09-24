import asyncio
import websockets
from shared.protocol import Protocol

class ChatServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients = set()

    async def broadcast(self, message, sender):
        for client in self.clients:
            if client != sender:
                await client.send(message)

    async def run(self):
        async with websockets.serve(self.handler, "127.0.0.1", self.port):
            print(f"[Server] Đang chạy tại ws://127.0.0.1:{self.port}")
            await asyncio.Future()

    async def handler(self, websocket):
        self.clients.add(websocket)
        remote = websocket.remote_address
        client_host = remote[0]
        client_port = remote[1]
        print(f"[Server] Một client đã kết nối từ {client_host}:{client_port}")
        try:
            async for message in websocket:
                packet = Protocol.parse_packet(message)
                print(f"[Server] Nhận: {packet}")

                if packet["cmd"] == "CHAT":
                    msg = Protocol.make_packet("CHAT", packet["data"])
                    await self.broadcast(msg, websocket)
        finally:
            self.clients.remove(websocket)
            print(f"[Server] Client {client_host}:{client_port} đã ngắt kết nối")

