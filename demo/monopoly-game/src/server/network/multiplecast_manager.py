import socket
import struct
from ..utils import logger
from .network_utils import udp_send


class MulticastManager:
    """
    Bộ điều hướng mạng (Network Router)
    -----------------------------------
    - Quản lý multicast group cho từng phòng.
    - Gửi packet đến đúng nhóm hoặc client cụ thể.
    - Hỗ trợ phân loại client: host, player, observer.
    """

    def __init__(self,logger_ins : 'logger', base_ip="239.0.0.0", base_port=5000):
        self.groups = {}  # { room_id: { "ip", "port", "socket", "clients": {id: info}} }
        self.base_ip = base_ip
        self.base_port = base_port
        self.ip_pool = self._generate_multicast_ip_pool()
        self.logger =logger_ins
        self.logger.info(message=f"[MULTICAST MANAGER] Initialized base={self.base_ip}:{self.base_port}")

    # --------------------------------------------------------------------------
    # 🧱 IP/Port Pool
    # --------------------------------------------------------------------------
    def _generate_multicast_ip_pool(self, start=1, end=254):
        """Sinh danh sách IP multicast khả dụng (239.x.x.x)."""
        base_parts = self.base_ip.split(".")
        base_prefix = ".".join(base_parts[:3])
        return [f"{base_prefix}.{i}" for i in range(start, end)]

    def _get_next_available_group(self):
        """Lấy IP + Port khả dụng cho phòng mới."""
        for ip in self.ip_pool:
            for port in range(self.base_port, self.base_port + 1000):
                if all((g["ip"], g["port"]) != (ip, port) for g in self.groups.values()):
                    return ip, port
        raise RuntimeError("Không còn IP/Port multicast khả dụng!")

    # --------------------------------------------------------------------------
    # 🏠 Group Management
    # --------------------------------------------------------------------------
    def create_group(self, room_id: str):
        """Tạo group multicast mới cho phòng."""
        if room_id in self.groups:
            return self.groups[room_id]

        ip, port = self._get_next_available_group()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', port))

            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(ip), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

            self.logger.info(message =f"[MULTICAST] Room {room_id} joined group {ip}:{port}")
        except OSError as e:
            self.logger.warning(f"[MULTICAST FALLBACK] Không thể join multicast ({e}). Dùng UDP thường.")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.groups[room_id] = {"ip": ip, "port": port, "socket": sock, "clients": {}}
        return self.groups[room_id]

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
            self.logger.info(message=f"[MULTICAST] Removed group {room_id} ({ip}:{port})")

    def list_groups(self):
        """Liệt kê tất cả group hiện có."""
        return {
            rid: {"ip": info["ip"], "port": info["port"], "client_count": len(info["clients"])}
            for rid, info in self.groups.items()
        }

    # --------------------------------------------------------------------------
    # 👥 Client Management
    # --------------------------------------------------------------------------
    def register_client(self, room_id: str, client_id: str, addr, role="player"):
        """
            Đăng ký client vào group multicast (dạng logical, không cần join socket).

            Args:
                room_id (str): ID của phòng game.
                client_id (str): ID định danh của client.
                addr (tuple): Địa chỉ IP và Port của client (ip, port).
                role (str, optional): Vai trò của client ("host" | "player" | "observer").
                                      Mặc định là "player".
            """
        group = self.groups.get(room_id)
        if not group:
            self.logger.error(f"[CLIENT REGISTER] Room {room_id} chưa có group multicast.")
            return
        group["clients"][client_id] = {"addr": addr, "role": role}
        self.logger.debug(message=f"[CLIENT REGISTER] {client_id} ({role}) joined {room_id} -> {addr}")

    def unregister_client(self, room_id: str, client_id: str):
        group = self.groups.get(room_id)
        if group and client_id in group["clients"]:
            del group["clients"][client_id]
            self.logger.debug(message=f"[CLIENT UNREGISTER] {client_id} left {room_id}")

    # --------------------------------------------------------------------------
    # 🚀 Packet Routing
    # --------------------------------------------------------------------------
    def send_packet(self, room_id: str, packet: dict, target="all", role=None):
        """
        Gửi packet đến nhóm hoặc người chơi cụ thể.
        :param room_id: Phòng đích
        :param packet: Dữ liệu dạng dict
        :param target: "all" | client_id
        :param role: Nếu chỉ muốn gửi cho "host"/"observer"/"player"
        """
        group = self.groups.get(room_id)
        if not group:
            self.logger.error(f"[MULTICAST SEND] Room {room_id} chưa có group.")
            return

        # Gửi multicast toàn phòng
        if target == "all":
            udp_send(group["socket"],packet, (group["ip"], group["port"]))
            self.logger.debug(message=f"[MULTICAST] Broadcast room {room_id} -> {group['ip']}:{group['port']}")
            return


        # Gửi unicast đến 1 client cụ thể hoặc theo vai trò
        for cid, info in group["clients"].items():
            if (target != "all" and cid == target) or (role and info["role"] == role):
                udp_send(group["socket"],packet, info["addr"])
                self.logger.debug(message=f"[UNICAST] {room_id} -> {cid} ({info['role']}) {info['addr']}")

    # --------------------------------------------------------------------------
    # 🧪 Debug
    # --------------------------------------------------------------------------
    def broadcast_test(self, room_id: str, message="ping"):
        packet = {"type": "TEST", "message": message, "room_id": room_id}
        self.send_packet(room_id, packet)

    def close_all_multicast_groups(self):
        """Đóng tất cả các socket multicast đã đăng ký."""
        for room_id, group in list(self.groups.items()):  # Dùng list() để duyệt và pop an toàn
            try:
                sock = group.get("socket")
                if sock:
                    sock.close()
                    self.logger.debug(f"[MULTICAST] Closed socket for room {room_id}")
                # Xóa khỏi danh sách group
                self.groups.pop(room_id, None)
            except Exception as e:
                self.logger.error(f"❌ Error closing socket for {room_id}: {e}")
