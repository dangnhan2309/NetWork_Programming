# src/server/game_server.py
import asyncio
import websockets
from typing import Dict, Set
from concurrent.futures import ThreadPoolExecutor

from ..shared.protocol import Protocol
from .room import GameRoom


class GameServer:
    """Main WebSocket server that manages rooms and clients."""
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.rooms: Dict[int, GameRoom] = {}
        self.next_room_id = 1
        self.executor = ThreadPoolExecutor(max_workers=4)  # if you want threading

    async def handler(self, websocket: websockets.WebSocketServerProtocol):
        """Handle client connection lifecycle."""
        print("[SERVER] Client connected")

        # Assign client to a room (for demo: auto-create one room)
        room_id = 1
        if room_id not in self.rooms:
            self.rooms[room_id] = GameRoom(room_id)
        room = self.rooms[room_id]

        try:
            async for message in websocket:
                packet = Protocol.parse_packet(message)
                action = packet.get("action")
                data = packet.get("data", {})

                print(f"[SERVER] Received: {action} {data}")

                # Example: simple JOIN / CHAT
                if action == "JOIN":
                    await room.add_client(websocket, data.get("name", "Unknown"))

                elif action == "CHAT":
                    await room.broadcast({"action": "CHAT", "data": data})

                elif action == "EXIT":
                    await room.remove_client(websocket)
                    break

                # Later: pass to GameManager
                else:
                    response = room.game.recieve_player_input(packet)
                    await room.broadcast({"action": "GAME", "data": response})

        except websockets.ConnectionClosed:
            print("[SERVER] Client disconnected")
        finally:
            await room.remove_client(websocket)

    async def start(self):
        print(f"[SERVER] Starting on {self.host}:{self.port}")
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # run forever
    def send_packet_clients(self,action,data):

        try :

            Protcol

        except Exception as e :
            print(e)


if __name__ == "__main__":
    server = GameServer()
    asyncio.run(server.start())
