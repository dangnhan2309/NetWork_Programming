"""
Quản lý các phòng chơi
"""

import random
from typing import Dict, List, Optional
from .game_manager import GameRoom
from ..shared.constants import *

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.room_counter = 1

    def create_room(self, room_name: str = None) -> GameRoom:
        """Tạo phòng mới"""
        room_id = f"room_{self.room_counter}"
        self.room_counter += 1
        
        if not room_name:
            room_name = f"Phòng {self.room_counter - 1}"
            
        room = GameRoom(room_id, room_name)
        self.rooms[room_id] = room
        
        # CHỈ IN 1 LẦN - bỏ print trong GameRoom.__init__
        print(f"🏠 Room created: {room_name} (ID: {room_id})")
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Lấy room theo ID"""
        return self.rooms.get(room_id)

    def get_available_rooms(self) -> List[dict]:
        """Lấy danh sách phòng có thể tham gia"""
        available_rooms = []
        for room in self.rooms.values():
            if len(room.players) < MAX_PLAYERS and room.state in [STATE_EMPTY, STATE_WAITING]:
                available_rooms.append(room.get_room_info())
        return available_rooms

    def get_random_available_room(self) -> Optional[GameRoom]:
        """Lấy ngẫu nhiên 1 phòng có thể tham gia"""
        available_rooms = []
        for room in self.rooms.values():
            if len(room.players) < MAX_PLAYERS and room.state in [STATE_EMPTY, STATE_WAITING]:
                available_rooms.append(room)
        
        return random.choice(available_rooms) if available_rooms else None

    def remove_empty_rooms(self):
        """Xóa các phòng trống"""
        empty_rooms = [room_id for room_id, room in self.rooms.items() if len(room.players) == 0]
        for room_id in empty_rooms:
            del self.rooms[room_id]
            print(f"🗑️ Removed empty room: {room_id}")