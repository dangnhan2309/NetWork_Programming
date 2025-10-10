import socket
import struct
import json
from typing import Tuple, Optional
from .port_checker import PortChecker

# ======================================================
# 🌐 GLOBAL PORT CHECKER (chỉ quét 1 lần duy nhất)
# ======================================================
PORT_CHECKER = None


# ======================================================
# 🧩 UDP SOCKET CREATION
# ======================================================
def create_udp_socket(multicast: bool = False, port: int = 0) -> socket.socket:
    """
    Tạo UDP socket và tự động chọn port khả dụng (nếu port=0)
    """
    global PORT_CHECKER

    # Khởi tạo PortChecker nếu chưa có
    if PORT_CHECKER is None:
        PORT_CHECKER = PortChecker(5000, 6000)
        PORT_CHECKER.scan_ports()

    # Nếu chưa có port được chỉ định, chọn ngẫu nhiên từ danh sách khả dụng
    if port == 0:
        port = PORT_CHECKER.get_random_port()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    if multicast:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    try:
        sock.bind(('', port))
        print(f"[UDP SOCKET] ✅ Bound to port {port}")
    except Exception as e:
        print(f"[UDP SOCKET] ❌ Failed to bind port {port}: {e}")
        raise e

    return sock


# ======================================================
# 📡 MULTICAST JOIN / LEAVE
# ======================================================
def join_multicast_group(sock: socket.socket, multicast_ip: str, port: int) -> bool:
    """
    Tham gia multicast group
    """
    try:
        mreq = socket.inet_aton(multicast_ip) + socket.inet_aton('0.0.0.0')
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"[JOINED MULTICAST] {multicast_ip}:{port}")
        return True
    except Exception as e:
        print(f"[JOIN ERROR] {e}")
        return False


def leave_multicast_group(sock: socket.socket, multicast_ip: str) -> bool:
    """
    Rời khỏi multicast group
    """
    try:
        local_ip = get_local_ip()
        group = socket.inet_aton(multicast_ip)
        iface = socket.inet_aton(local_ip)
        mreq = struct.pack("=4s4s", group, iface)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        return True
    except Exception as e:
        print(f"❌ Error leaving multicast group {multicast_ip}: {e}")
        return False


# ======================================================
# 📤 / 📥 SEND + RECEIVE UDP
# ======================================================
def send_udp(sock: socket.socket, data: dict, host: str, port: int) -> bool:
    try:
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data = data.encode('utf-8')

        sock.sendto(data, (host, port))
        return True
    except Exception as e:
        print(f"❌ Error sending UDP to {host}:{port}: {e}")
        return False


def receive_udp(sock: socket.socket, buffer_size: int = 4096, timeout: Optional[float] = None) -> Tuple[Optional[dict], Optional[Tuple[str, int]]]:
    try:
        if timeout is not None:
            sock.settimeout(timeout)

        data, addr = sock.recvfrom(buffer_size)
        try:
            json_data = json.loads(data.decode('utf-8'))
            return json_data, addr
        except json.JSONDecodeError:
            return {"raw_data": data.decode('utf-8')}, addr

    except socket.timeout:
        return None, None
    except Exception as e:
        print(f"❌ Error receiving UDP: {e}")
        return None, None


# ======================================================
# ⚙️ UTILS
# ======================================================
def get_available_port(start_port: int = 5000, end_port: int = 6000) -> int:
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available ports between {start_port}-{end_port}")


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
