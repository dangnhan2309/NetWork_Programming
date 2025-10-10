import asyncio
from ..utils.network_utils import create_udp_socket
from ..utils.port_checker import PortChecker

class RoomManager:
    """
    Quản lý các phòng trong game Monopoly - ĐÃ SỬA HOÀN TOÀN
    """

    def __init__(self, logger):
        self.logger = logger
        self.rooms = {}  # { room_id: {players, multicast_ip, port, socket} }
        self.port_checker = PortChecker(5000, 6000)
        self.port_checker.scan_ports()

    async def create_room(self, room_id: str):
        """Tạo phòng mới - CHỈ trả về thông tin có thể serialize"""
        if room_id in self.rooms:
            self.logger.warning(f"⚠️ Room '{room_id}' already exists.")
            return None

        multicast_ip = f"224.1.1.{len(self.rooms) + 10}"
        port = self.port_checker.get_random_port()
        sock = create_udp_socket(multicast=True, port=port)

        # Lưu thông tin đầy đủ (có socket) trong internal storage
        self.rooms[room_id] = {
            "room_id": room_id,
            "multicast_ip": multicast_ip,
            "port": port,
            "socket": sock,  # socket object, không serialize được
            "players": []
        }

        self.logger.success(f"🏠 Created room '{room_id}' on {multicast_ip}:{port}")
        
        # QUAN TRỌNG: Chỉ trả về thông tin có thể serialize
        return {
            "room_id": room_id,
            "multicast_ip": multicast_ip,
            "port": port,
            "players": []
        }

    async def list_rooms(self):
        """Trả về danh sách phòng dưới dạng dict có thể serialize"""
        result = {}
        for rid, info in self.rooms.items():
            result[rid] = {
                "multicast_ip": info["multicast_ip"],
                "port": info["port"],
                "players": info["players"]  # Chỉ các field có thể serialize
            }
        return result

    async def add_player(self, room_id: str, player_name: str):
        """Thêm người chơi vào phòng - Trả về info có thể serialize"""
        if room_id not in self.rooms:
            self.logger.warning(f"Room '{room_id}' not found.")
            return None

        room = self.rooms[room_id]
        if player_name not in room["players"]:
            room["players"].append(player_name)
            self.logger.info(f"👤 {player_name} joined {room_id}")
        
        # QUAN TRỌNG: Chỉ trả về thông tin có thể serialize
        return {
            "room_id": room_id,
            "multicast_ip": room["multicast_ip"],
            "port": room["port"],
            "players": room["players"].copy()  # Copy để tránh reference
        }

    async def remove_player(self, room_id: str, player_name: str):
        """Xóa người chơi khỏi phòng"""
        if room_id in self.rooms and player_name in self.rooms[room_id]["players"]:
            self.rooms[room_id]["players"].remove(player_name)
            self.logger.info(f"👋 {player_name} left {room_id}")
            return True
        return False

    def get_room_info(self, room_id: str):
        """Lấy thông tin room (có socket) cho internal use"""
        return self.rooms.get(room_id)