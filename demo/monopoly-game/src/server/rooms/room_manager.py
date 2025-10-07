import json
import os
import threading
import random
from datetime import datetime
from ..utils import logger
from ..network import network_utils


class RoomManager:
    """
    Quản lý danh sách phòng chơi (room) trong Monopoly.
    Mỗi phòng có: room_id, multicast_ip, port, player_list, socket, created_at.
    """

    def __init__(self, data_file="rooms_data.json", max_players_per_room=4):
        self.data_file = data_file
        self.max_players_per_room = max_players_per_room
        self.rooms = {}
        self.lock = threading.Lock()

        self._load_from_file()
        logger.info("[ROOM MANAGER] Initialized.")

    # ----------------------------------------------------------------------
    def _save_to_file(self):
        """Lưu danh sách phòng ra file JSON."""
        try:
            with self.lock:
                serializable_rooms = {}
                for rid, room in self.rooms.items():
                    serializable_rooms[rid] = {
                        "room_id": room["room_id"],
                        "multicast_ip": room["multicast_ip"],
                        "port": room["port"],
                        "players": room["players"],
                        "max_players": room["max_players"],
                        "created_at": room["created_at"],
                    }
                with open(self.data_file, "w", encoding="utf-8") as f:
                    json.dump(serializable_rooms, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[ROOM SAVE ERROR] {e}")

    # ----------------------------------------------------------------------
    def _load_from_file(self):
        """Đọc danh sách phòng từ file JSON nếu có."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    loaded_rooms = json.load(f)
                    for rid, room_info in loaded_rooms.items():
                        # Socket không thể lưu nên phải tạo lại
                        room_info["socket"] = None
                        self.rooms[rid] = room_info
                logger.info(f"[ROOM LOADED] Loaded {len(self.rooms)} rooms.")
            except Exception as e:
                logger.error(f"[ROOM LOAD ERROR] {e}")
                self.rooms = {}

    # ----------------------------------------------------------------------
    def _generate_multicast_ip(self):
        """Tạo địa chỉ multicast ngẫu nhiên (224.0.1.0 - 239.255.255.255)."""
        return f"239.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

    def _generate_port(self):
        """Tạo port ngẫu nhiên trong khoảng an toàn."""
        return random.randint(10000, 60000)

    # ----------------------------------------------------------------------
    def create_room(self, room_id: str):
        """
        Tạo phòng mới, cấp multicast IP/port và socket.
        """
        with self.lock:
            if room_id in self.rooms:
                logger.warning(f"[ROOM CREATE] Room {room_id} already exists.")
                return self.rooms[room_id]

            multicast_ip = self._generate_multicast_ip()
            port = self._generate_port()

            udp_sock = network_utils.create_udp_socket(multicast=True)
            network_utils.join_multicast_group(udp_sock, multicast_ip)

            room_info = {
                "room_id": room_id,
                "multicast_ip": multicast_ip,
                "port": port,
                "players": [],
                "max_players": self.max_players_per_room,
                "created_at": datetime.utcnow().isoformat(),
                "socket": udp_sock,
            }

            self.rooms[room_id] = room_info
            self._save_to_file()

            logger.info(f"[ROOM CREATED] {room_id} → {multicast_ip}:{port}")
            return room_info

    # ----------------------------------------------------------------------
    def delete_room(self, room_id: str):
        """Xóa phòng và đóng socket multicast."""
        with self.lock:
            if room_id not in self.rooms:
                logger.warning(f"[ROOM DELETE] {room_id} not found.")
                return False

            room = self.rooms[room_id]
            sock = room.get("socket")
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

            del self.rooms[room_id]
            self._save_to_file()
            logger.info(f"[ROOM DELETED] {room_id}")
            return True

    # ----------------------------------------------------------------------
    def add_player(self, room_id: str, player_name: str):
        """Thêm người chơi vào phòng."""
        with self.lock:
            if room_id not in self.rooms:
                logger.warning(f"[ROOM ADD] Room {room_id} not found.")
                return None

            room = self.rooms[room_id]
            if len(room["players"]) >= room["max_players"]:
                logger.warning(f"[ROOM FULL] Room {room_id} is full.")
                return None

            if player_name in room["players"]:
                logger.info(f"[ROOM] {player_name} already in {room_id}")
                return room

            room["players"].append(player_name)
            self._save
