# src/shared/network_utils.py

import json
import socket
import random
import string
from datetime import datetime
from typing import Dict, Tuple, Union

# ========================
# Utility Functions
# ========================

def generate_id(length: int = 6) -> str:
    """Tạo ID ngẫu nhiên gồm chữ hoa + số."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def timestamp() -> str:
    """Trả về timestamp hiện tại dạng HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")


def encode_packet(data: Dict) -> bytes:
    """Chuyển dict thành bytes để gửi qua mạng."""
    return json.dumps(data).encode("utf-8")


def decode_packet(packet: bytes) -> Dict:
    """Chuyển bytes nhận được thành dict."""
    try:
        return json.loads(packet.decode("utf-8"))
    except json.JSONDecodeError:
        return {}

# ========================
# UDP Functions
# ========================

def udp_send(sock: socket.socket, data: Dict, ip: str, port: int) -> None:
    """Gửi dict qua UDP."""
    pkt = encode_packet(data)
    sock.sendto(pkt, (ip, port))

: udp_send(self.sock, packet, (self.group_ip, self.port))

def udp_receive(sock: socket.socket, buffer_size: int = 4096) -> Tuple[Dict, Tuple[str, int]]:
    """
    Nhận packet UDP và decode.
    Trả về (dict, (ip, port))
    """
    pkt, addr = sock.recvfrom(buffer_size)
    data = decode_packet(pkt)
    return data, addr


def create_udp_socket(multicast: bool = False, ttl: int = 2) -> socket.socket:
    """Tạo UDP socket, có hỗ trợ multicast nếu cần."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if multicast:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    return sock


def join_multicast_group(sock: socket.socket, multicast_ip: str, iface_ip: str = "0.0.0.0") -> None:
    """Tham gia multicast group."""
    mreq = socket.inet_aton(multicast_ip) + socket.inet_aton(iface_ip)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
