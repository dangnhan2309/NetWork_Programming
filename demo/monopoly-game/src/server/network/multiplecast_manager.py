# src/server/network/multicast_manager.py
import socket
import struct
import random
from typing import Dict, Optional
from ..utils.logger import Logger
from ..utils.packet_format import PacketFormat
from ..utils.network_utils import udp_send

class MulticastManager:
    """
    Quản lý danh sách multicast group cho từng phòng game.
    Mỗi phòng tương ứng với một group (IP + Port).
    """

    def __init__(self, base_ip="239.0.0.0", base_port=5000):
        """
        :param base_ip: IP multicast bắt đầu (224.0.0.0 – 239.255.255.255)
        :param base_port: Port bắt đầu cho multicast
        """
        self.groups = {}      
        self.base_ip = base_ip
        self.base_port = base_port
        self.ip_pool = self._generate_multicast_ip_pool()
        self.logger = Logger("MulticastManager")
    # --------------------------------------------------------------------------
    def _generate_multicast_ip_pool(self, start=1, end=254):
        """Sinh danh sách IP multicast khả dụng (239.x.x.x)."""
        base_parts = self.base_ip.split(".")
        base_prefix = ".".join(base_parts[:3])
        return [f"{base_prefix}.{i}" for i in range(start, end)]

    # --------------------------------------------------------------------------
    def _get_next_available_group(self):
        """Lấy IP + Port khả dụng cho phòng mới."""
        for ip in self.ip_pool:
            for port in range(self.base_port, self.base_port + 1000):
                if (ip, port) not in [(g["ip"], g["port"]) for g in self.groups.values()]:
                    return ip, port
        raise RuntimeError("Không còn IP/Port multicast khả dụng!")

    # --------------------------------------------------------------------------
    def create_group(self, room_id: str, multicast_ip: str = None, port: int = None):
        """Tạo group multicast mới cho phòng - TẮT LOOPBACK"""
        if room_id in self.groups:
            return self.groups[room_id]

        if not multicast_ip or not port:
            multicast_ip, port = self._get_next_available_group()

        self.logger.info(f"[MULTICAST] Creating group for {room_id} at {multicast_ip}:{port}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # BIND SOCKET
            sock.bind(('', port))
            self.logger.debug(f"[MULTICAST] Socket bound to port {port}")

            # THAM GIA MULTICAST GROUP - TẮT LOOPBACK
            mreq = struct.pack("4sl", socket.inet_aton(multicast_ip), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # QUAN TRỌNG: TẮT LOOPBACK để server không nhận lại chính message của mình
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
            
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            # ĐẶT SOCKET THÀNH NON-BLOCKING
            sock.setblocking(False)
            
            self.logger.info(f"[MULTICAST] ✅ Room {room_id} joined group {multicast_ip}:{port} (loopback disabled)")
            
        except OSError as e:
            self.logger.warning(f"[MULTICAST FALLBACK] Không thể join multicast ({e}). Dùng UDP thường.")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)

        group_info = {"ip": multicast_ip, "port": port, "socket": sock}
        self.groups[room_id] = group_info
        
        return group_info
    # --------------------------------------------------------------------------
    def get_group(self, room_id: str) -> Optional[Dict]:
        """Lấy thông tin multicast group của phòng."""
        return self.groups.get(room_id)

    # --------------------------------------------------------------------------
    def remove_group(self, room_id: str):
        """Xóa group multicast khi phòng kết thúc."""
        group = self.groups.pop(room_id, None)
        if not group:
            self.logger.warning(f"[MULTICAST] Group {room_id} không tồn tại để xóa.")
            return

        ip, port, sock = group["ip"], group["port"], group["socket"]
        try:
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        except OSError:
            pass
        finally:
            sock.close()
            self.logger.info(f"[MULTICAST] Removed group {room_id} ({ip}:{port})")

    # --------------------------------------------------------------------------
    def list_groups(self) -> Dict:
        """Liệt kê tất cả group hiện có."""
        return {
            rid: {"ip": info["ip"], "port": info["port"]}
            for rid, info in self.groups.items()
        }

    # --------------------------------------------------------------------------
    def broadcast_packet(self, room_id: str, packet_type: str, payload: dict, sender="server", action=None):
        """Hàm chung để broadcast mọi loại packet"""
        try:
            packet = PacketFormat.create_packet(
                packet_type=packet_type,
                room_id=room_id,
                sender=sender,
                target="all",
                action=action or packet_type,
                payload=payload
            )
            return self.broadcast_to_room(room_id, packet)
        except Exception as e:
            self.logger.error(f"[MULTICAST] Lỗi broadcast {packet_type}: {e}")
            return False



    # --------------------------------------------------------------------------
    def broadcast_test(self, room_id: str, message="ping"):
        """Gửi test message multicast đến group (nếu cần kiểm tra)."""
        group = self.get_group(room_id)
        if not group:
            self.logger.error(f"[MULTICAST TEST] Room {room_id} chưa có group.")
            return
        
        packet = PacketFormat.create_packet(
            packet_type="test",
            room_id=room_id,
            sender="server",
            target="all",
            action="test_message",
            payload={"message": message, "status": "test"}
        )
        
        udp_send(group["socket"], packet, (group["ip"], group["port"]))
        self.logger.debug(f"[MULTICAST TEST] Sent to {group['ip']}:{group['port']} -> {message}")

    # --------------------------------------------------------------------------
    def get_group_socket(self, room_id: str) -> Optional[socket.socket]:
        """Lấy socket multicast của phòng."""
        group = self.get_group(room_id)
        return group["socket"] if group else None

    # --------------------------------------------------------------------------
    def get_active_rooms_count(self) -> int:
        """Lấy số lượng phòng đang có multicast active."""
        return len(self.groups)

    # --------------------------------------------------------------------------
    def is_room_active(self, room_id: str) -> bool:
        """Kiểm tra phòng có multicast active không."""
        return room_id in self.groups

    # --------------------------------------------------------------------------
    def cleanup_all_groups(self):
        """Dọn dẹp tất cả multicast groups."""
        for room_id in list(self.groups.keys()):
            self.remove_group(room_id)
        self.logger.info("[MULTICAST] Đã dọn dẹp tất cả groups")