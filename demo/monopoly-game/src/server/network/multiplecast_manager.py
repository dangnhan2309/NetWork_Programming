import socket
import struct
import random
from ..utils import logger
from .network_utils import udp_send

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
        self.groups = {}       # { room_id: {"ip": str, "port": int, "socket": socket.socket} }
        self.base_ip = base_ip
        self.base_port = base_port
        self.ip_pool = self._generate_multicast_ip_pool()
        self.used_ports = set()
        logger.info(f"[MULTICAST MANAGER] Initialized base={self.base_ip}:{self.base_port}")

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
    def create_group(self, room_id: str):
        """Tạo group multicast mới cho phòng."""
        if room_id in self.groups:
            return self.groups[room_id]

        ip, port = self._get_next_available_group()

        # Tạo socket multicast
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', port))

            # Tham gia group multicast
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

            logger.info(f"[MULTICAST] Room {room_id} joined group {ip}:{port}")
        except OSError as e:
            logger.warning(f"[MULTICAST FALLBACK] Không thể join multicast ({e}). Dùng UDP thường.")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.groups[room_id] = {"ip": ip, "port": port, "socket": sock}
        return self.groups[room_id]

    # --------------------------------------------------------------------------
    def get_group(self, room_id: str):
        """Lấy thông tin multicast group của phòng."""
        return self.groups.get(room_id)

    # --------------------------------------------------------------------------
    def remove_group(self, room_id: str):
        """Xóa group multicast khi phòng kết thúc."""
        group = self.groups.pop(room_id, None)
        if not group:
            logger.warning(f"[MULTICAST] Group {room_id} không tồn tại để xóa.")
            return

        ip, port, sock = group["ip"], group["port"], group["socket"]
        try:
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        except OSError:
            pass
        finally:
            sock.close()
            logger.info(f"[MULTICAST] Removed group {room_id} ({ip}:{port})")

    # --------------------------------------------------------------------------
    def list_groups(self):
        """Liệt kê tất cả group hiện có."""
        return {
            rid: {"ip": info["ip"], "port": info["port"]}
            for rid, info in self.groups.items()
        }

    # --------------------------------------------------------------------------
    def broadcast_test(self, room_id: str, message="ping"):
        """Gửi test message multicast đến group (nếu cần kiểm tra)."""
        group = self.get_group(room_id)
        if not group:
            logger.error(f"[MULTICAST TEST] Room {room_id} chưa có group.")
            return
        packet = {"type": "TEST", "message": message, "room_id": room_id}
        udp_send(group["socket"], (group["ip"], group["port"]), packet)
        logger.debug(f"[MULTICAST TEST] Sent to {group['ip']}:{group['port']} -> {message}")


# --------------------------------------------------------------------------
if __name__ == "__main__":
    """Test nhanh cơ chế tạo / broadcast / xóa multicast group."""
    import time

    manager = MulticastManager()

    g1 = manager.create_group("ROOM_01")
    g2 = manager.create_group("ROOM_02")

    print(manager.list_groups())

    manager.broadcast_test("ROOM_01", "Hello Room 1!")
    manager.broadcast_test("ROOM_02", "Welcome Room 2!")

    time.sleep(1)
    manager.remove_group("ROOM_01")
    print(manager.list_groups())
