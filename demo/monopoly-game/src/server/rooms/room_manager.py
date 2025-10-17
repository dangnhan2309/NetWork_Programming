# src/server/rooms/room_manager.py
import random
import time
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, List

from ..utils.port_checker import PortChecker
from ..utils.logger import Logger

@dataclass
class Room:
    room_id: str
    room_name: str
    host_name: str
    max_players: int
    players: List[str] = field(default_factory=list)
    multicast_ip: str = ""
    port: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    game_started: bool = False
    game_state: dict = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class RoomManager:
    """
    Quản lý tất cả các phòng trong game Monopoly
    """

    def __init__(self, logger: Logger, multicast_manager=None):
        self.logger = logger
        self.rooms: Dict[str, Room] = {}
        self.port_checker = PortChecker(5000, 6000)
        self.multicast_manager = multicast_manager
        self._multicast_counter = 10  # dùng để cấp multicast IP
        self._global_lock = asyncio.Lock()  # lock global cho self.rooms
        self.logger.info("🏠 RoomManager initialized")

    # ========================
    # Room Creation / Listing
    # ========================
    async def create_room(
        self,
        room_id: str,
        room_name: str,
        host_name: str,
        max_players: int = 4,
    ) -> Optional[Room]:
        async with self._global_lock:
            if room_id in self.rooms:
                self.logger.warning(f"⚠️ Room {room_id} already exists")
                return None

            port = self.port_checker.get_random_port()
            if port is None:
                self.logger.error("❌ Không thể lấy port khả dụng")
                return None

            multicast_ip = f"239.0.0.{self._multicast_counter}"
            self._multicast_counter += 1

            room = Room(
                room_id=room_id,
                room_name=room_name,
                host_name=host_name,
                max_players=max_players,
                players=[host_name],
                multicast_ip=multicast_ip,
                port=port,
            )

            self.rooms[room_id] = room
            self.logger.info(
                f"🏠 Created room {room_name} ({room_id}) - Max {max_players} players - Multicast: {multicast_ip}:{port}"
            )
            return room

    async def list_rooms(self) -> Dict[str, dict]:
        result = {}
        async with self._global_lock:
            for rid, room in self.rooms.items():
                result[rid] = {
                    "room_name": room.room_name,
                    "host_name": room.host_name,
                    "multicast_ip": room.multicast_ip,
                    "port": room.port,
                    "players": room.players.copy(),
                    "max_players": room.max_players,
                    "game_started": room.game_started,
                }
        return result

    # ========================
    # Player Management
    # ========================
    async def add_player(self, room_id: str, player_name: str) -> Optional[dict]:
        room = self.rooms.get(room_id)
        if not room:
            self.logger.warning(f"Room '{room_id}' not found.")
            return None

        async with room.lock:
            if len(room.players) >= room.max_players:
                self.logger.warning(f"❌ Room '{room_id}' is full ({room.max_players} players).")
                return None

            if player_name not in room.players:
                room.players.append(player_name)
                self.logger.info(f"👤 {player_name} joined {room_id}")

        return {
            "room_id": room.room_id,
            "room_name": room.room_name,
            "host_name": room.host_name,
            "multicast_ip": room.multicast_ip,
            "port": room.port,
            "players": room.players.copy(),
            "max_players": room.max_players,
            "game_started": room.game_started,
            "is_host": room.host_name == player_name,
        }

    async def remove_player(self, room_id: str, player_name: str) -> bool:
        room = self.rooms.get(room_id)
        if not room:
            return False

        async with room.lock:
            if player_name in room.players:
                room.players.remove(player_name)
                self.logger.info(f"👋 {player_name} left {room_id}")

                if len(room.players) == 0:
                    # Tự động xóa phòng khi trống
                    await self.remove_room(room_id)

                return True
        return False

    async def find_best_room(self, player_name: str) -> Optional[str]:
        async with self._global_lock:
            available_rooms = [
                r for r in self.rooms.values()
                if len(r.players) < r.max_players and not r.game_started
            ]
        if not available_rooms:
            return None
        # Chọn phòng gần full nhất
        available_rooms.sort(key=lambda r: len(r.players), reverse=True)
        return available_rooms[0].room_id

    # ========================
    # Game Control
    # ========================
    def can_start_game(self, room_id: str, min_players: int = 2) -> bool:
        room = self.rooms.get(room_id)
        if not room:
            return False
        return len(room.players) >= min_players and not room.game_started

    async def start_game(self, room_id: str, initial_state: dict = None) -> dict:
        room = self.rooms.get(room_id)
        if not room:
            return {"success": False, "message": f"Room {room_id} not found."}

        async with room.lock:
            if room.game_started:
                self.logger.warning(f"⚠️ Game in room {room_id} already started.")
                return {"success": True, "message": "Game đã được bắt đầu trước đó!"}

            if not self.can_start_game(room_id):
                player_count = len(room.players)
                return {
                    "success": False,
                    "message": f"Không thể bắt đầu game: cần tối thiểu 2 người chơi ({player_count}/{room.max_players}).",
                }

            room.game_started = True
            room.game_state = initial_state or {}
            if "players" not in room.game_state:
                room.game_state["players"] = room.players.copy()

            self.logger.info(f"🎮 Game started in room {room_id}")

            if self.multicast_manager:
                await self.multicast_manager.broadcast_game_started(room_id)
                await self.multicast_manager.broadcast_state(room_id, room.game_state)

            return {"success": True, "message": "Game đã bắt đầu thành công!"}

    # ========================
    # Room Removal / Cleanup
    # ========================
    async def remove_room(self, room_id: str) -> bool:
        async with self._global_lock:
            room = self.rooms.get(room_id)
            if room:
                self.port_checker.release_port(room.port)
                del self.rooms[room_id]
                self.logger.info(f"🗑️ Removed room {room_id} and released port {room.port}")
                return True
        return False

    # ========================
    # Multicast Management
    # ========================
    async def setup_room_multicast(self, room_id: str) -> bool:
        room = self.rooms.get(room_id)
        if not room or not self.multicast_manager:
            self.logger.warning(f"⚠️ Cannot setup multicast for {room_id}")
            return False

        async with room.lock:
            try:
                if not self.multicast_manager.is_room_active(room_id):
                    group_info = self.multicast_manager.create_group(room_id, room.multicast_ip, room.port)
                    if group_info:
                        self.logger.info(f"✅ Multicast setup for {room_id}: {room.multicast_ip}:{room.port}")
                        return True
                    else:
                        self.logger.error(f"❌ Failed to setup multicast for {room_id}")
                        return False
                else:
                    self.logger.info(f"✅ Multicast already active for {room_id}")
                    return True
            except Exception as e:
                self.logger.error(f"❌ Error setting up multicast for {room_id}: {e}")
                return False

    def get_room_multicast_info(self, room_id: str) -> Tuple[Optional[str], Optional[int]]:
        room = self.rooms.get(room_id)
        if room:
            return room.multicast_ip, room.port
        return None, None

    # ========================
    # Auto-create Room
    # ========================
    async def auto_create_room(self, player_name: str) -> Optional[Room]:
        current_time = int(time.time())
        random_suffix = random.randint(1000, 9999)
        room_id = f"AUTO_{current_time}_{random_suffix}"
        room_name = f"Phòng-Nhanh-{random.randint(1000,9999)}"
        max_players = random.choice([2, 4, 6])
        self.logger.info(f"🎯 Creating auto room: {room_name} for {player_name}")
        return await self.create_room(room_id, room_name, player_name, max_players)
