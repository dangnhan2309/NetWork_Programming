import asyncio

from .game_manager import GameManager
from ..shared.protocol import Protocol
import websockets
from typing import Dict, Set

class GameRoom:
    """Manage one game room with multiple players."""
    def __init__(self, room_id: int):
        self.room_id = room_id
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.game = GameManager()
        self.loop_task = None
        self.room_capacity = 4
        self.state_room = False# background game loop task
        
    async def start_loop(self):
        """Run the game loop asynchronously."""
        print(f"[ROOM {self.room_id}] Game started")
        while True:
            await asyncio.sleep(2)  # example "tick" every 2 seconds
            state = self.game.game_handler()
            if state:
                await self.broadcast({"action": "GAME_STATE", "data": state})

    def ensure_started(self):
        """Make sure the game loop runs once room is created."""
        if self.loop_task is None:
            self.loop_task = asyncio.create_task(self.start_loop())

    async def broadcast(self, packet: Dict):
        """Send message to all players in this room."""
        msg = Protocol.make_packet(packet["action"], packet["data"])
        await asyncio.gather(
            *[client.send(msg) for client in self.clients if not client.close],
            return_exceptions=True
        )
    def check_slots(self):
        slots =self.room_capacity- self.clients.__len__()
        if slots > 0   :
            print(f"[Check_slots]Room still have {slots} slots available !!")
            return True
        else :
            return False

    async def add_client(self, websocket, name: str):
        if self.check_slots():
            self.clients.add(websocket)
            await self.broadcast({"action": "CHAT", "data": {"msg": f"A player name {name} join "}})
            # GỬI SAI HOĂC CLIENT CHƯA CÓ SỬ LÍ REQUEST
            return True
        else :
            return False




    async def remove_client(self, websocket):
        if websocket in self.clients:
            self.clients.remove(websocket)
            await self.broadcast({"action": "EXIT", "data": {"msg": "A player left"}})
