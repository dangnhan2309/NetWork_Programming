# network/network_utils.py
"""
Network Utilities Module
------------------------
Hỗ trợ gửi / nhận gói tin mạng (TCP, UDP, Multicast) theo chuẩn packet_format
Tự động:
- Encode / Decode / Validate gói tin
- Ghi log chi tiết (send / recv)
- Fallback sang JSON nếu packet_format gặp lỗi
"""

import socket
import json
from json import JSONDecodeError

from ..utils import packetformat
from ..utils import logger

logger = logger("network_utils")


# ============================================================
# 🧱 CORE ENCODE / DECODE LAYER
# ============================================================
def encode_packet(packet: dict) -> bytes:
    """Encode packet theo chuẩn utils.packet_format, fallback sang JSON"""
    try:
        return packetformat.encode_packet(packet)
    except Exception as e:
        logger.warning(f"Packet format encode lỗi ({e}), fallback sang JSON.")
        try:
            return json.dumps(packet).encode("utf-8")
        except Exception as e2:
            logger.error(f"Encode JSON thất bại: {e2}")
            return b""


def decode_packet(data: bytes) -> dict | None:
        """Decode packet, fallback to JSON if initial decode fails."""

        # --- FIRST ATTEMPT: Custom Packet Format ---
        try:
            # Assuming packetformat.decode_packet raises some form of ValueError
            # or custom decoding error when data is corrupt.
            return packetformat.decode_packet(data)

            # Catch specific errors for the packet format failure.
        # We use a broad base exception (like ValueError) if we don't know the custom error name.
        except (ValueError, TypeError) as e:
            logger.debug(f"Custom decode failed ({e}). Attempting JSON fallback.")

        # --- SECOND ATTEMPT: JSON Fallback ---
        try:
            # 1. Decode bytes to string
            decoded_string = data.decode("utf-8")

            # 2. Parse JSON
            return json.loads(decoded_string)

        # Catch specific errors for JSON failure
        except (JSONDecodeError, UnicodeDecodeError) as e:
            # This is the final expected failure point for bad data format
            logger.warning(f"JSON decode failed. Data is unusable ({e}), skipping.")
            return None


# ============================================================
# ⚙️ VALIDATION & LOGGING
# ============================================================
def validate_packet(packet: dict) -> bool:
    # nếu có header/payload kiểu PacketFormat
    if "header" in packet and "payload" in packet:
        return True
    # fallback cũ
    required = ["type", "data", "timestamp"]
    missing = [f for f in required if f not in packet]
    if missing:
        logger.debug(f"Gói tin thiếu trường: {missing}")
        return False
    return True


def log_packet(packet: dict, action: str, addr=None):
    """Ghi log gói tin gửi / nhận"""
    prefix = f"[{action.upper()}]"
    addr_info = f" | from {addr}" if addr else ""
    pkt_type = packet.get("type", "unknown")
    # SỬA: sử dụng logger thay vì logger.log_packet
    logger.info(f"{prefix} {pkt_type}{addr_info}")


# ============================================================
# 🌐 TCP FUNCTIONS
# ============================================================
def tcp_send(sock: socket.socket, packet: dict):
    """Gửi packet qua TCP"""
    try:
        encoded = encode_packet(packet)
        sock.sendall(encoded)
        log_packet(packet, "SEND-TCP")
    except Exception as e:
        logger.error(f"Lỗi TCP send: {e}")


def tcp_receive(sock: socket.socket, buffer_size=4096) -> dict | None:
    """Nhận packet TCP"""
    try:
        data = sock.recv(buffer_size)
        if not data:
            return None
        packet = decode_packet(data)
        if validate_packet(packet):
            log_packet(packet, "RECV-TCP")
            return packet
        return None
    except Exception as e:
        logger.error(f"Lỗi TCP receive: {e}")
        return None


# ============================================================
# 📡 UDP / MULTICAST FUNCTIONS
# ============================================================
def udp_send(sock: socket.socket, packet: dict, addr: tuple):
    """
    Gửi packet qua UDP hoặc Multicast.

    Args:
        sock: socket UDP đã bind / join multicast.
        packet: dict packet theo chuẩn PacketFormat.
        addr: tuple(IP, port) của đích đến.

    Notes for deployment:
        - packet được encode sang JSON trước khi gửi.
        - Sau khi gửi, packet được log để dễ quan sát
          luồng dữ liệu trong môi trường production.
        - Giữ log để debug các lỗi multicast / UDP.
    """
    try:
        encoded = packetformat.encode_packet(packet)  # encode packet
        sock.sendto(encoded, addr)
        # Log packet gửi: nội dung + địa chỉ
        logger.log_packet("SEND", addr, packet)
    except Exception as e:
        logger.error(f"Lỗi UDP send tới {addr}: {e}")


def udp_receive(sock: socket.socket, buffer_size=4096) -> tuple[dict | None, tuple | None]:
    """
    Nhận packet từ UDP hoặc Multicast.

    Args:
        sock: socket UDP đã bind / join multicast.
        buffer_size: kích thước buffer tối đa để nhận packet.

    Returns:
        (packet dict, addr tuple) nếu packet hợp lệ,
        (None, addr) nếu packet không hợp lệ,
        (None, None) nếu lỗi trong quá trình nhận.

    Notes for deployment:
        - Packet sẽ được decode từ JSON sang dict.
        - Packet hợp lệ sẽ được log chi tiết.
        - Packet không hợp lệ chỉ log cảnh báo, không làm gián đoạn server.
    """
    try:
        data, addr = sock.recvfrom(buffer_size)
        packet = packetformat.decode_packet(data)
        if packetformat.is_valid(packet):
            # Log packet nhận: nội dung + địa chỉ
            logger.log_packet("RECV", addr, packet)
            return packet, addr
        logger.warning(f"Gói tin không hợp lệ từ {addr}")
        return None, addr
    except Exception as e:
        logger.error(f"Lỗi UDP receive: {e}")
        return None, None
# ============================================================
# 🧠 HIGH-LEVEL HELPERS
# ============================================================
def send(sock: socket.socket, packet: dict, addr=None, protocol="auto"):
    """
    Hàm gửi linh hoạt:
    - protocol = 'tcp' hoặc 'udp'
    - nếu auto: xác định theo socket type
    """
    if protocol == "tcp" or (protocol == "auto" and sock.type == socket.SOCK_STREAM):
        tcp_send(sock, packet)
    else:
        if addr is None:
            raise ValueError("UDP cần địa chỉ đích (addr)")
        udp_send(sock, packet, addr)


def receive(sock: socket.socket, protocol="auto", buffer_size=4096):
    """
    Hàm nhận linh hoạt:
    - Tự động nhận TCP hoặc UDP
    """
    if protocol == "tcp" or (protocol == "auto" and sock.type == socket.SOCK_STREAM):
        return tcp_receive(sock)
    else:
        return udp_receive(sock, buffer_size)


# ============================================================
# 🔍 UTILITIES
# ============================================================
def create_udp_socket(multicast=False, reuse=True, ttl=1):
    """Tạo UDP hoặc Multicast socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if reuse:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if multicast:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    return sock


def join_multicast_group(sock: socket.socket, mcast_ip: str):
    """Tham gia nhóm multicast"""
    import struct
    try:
        mreq = struct.pack("4sl", socket.inet_aton(mcast_ip), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        logger.info(f"Đã join group multicast {mcast_ip}")
    except Exception as e:
        logger.error(f"Không thể join group {mcast_ip}: {e}")


def leave_multicast_group(sock: socket.socket, mcast_ip: str):
    """Rời khỏi nhóm multicast"""
    import struct
    try:
        mreq = struct.pack("4sl", socket.inet_aton(mcast_ip), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        logger.info(f"Đã rời group multicast {mcast_ip}")
    except Exception as e:
        logger.error(f"Không thể rời group {mcast_ip}: {e}")
def create_tcp_server(host: str, port: int, backlog=5) -> socket.socket:
    """
    Tạo TCP server socket, bind và listen.
    Trả về socket đã bind sẵn.
    """
    try:
        srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv_sock.bind((host, port))
        srv_sock.listen(backlog)
        logger.info(f"TCP server listening on {host}:{port}")
        return srv_sock
    except Exception as e:
        logger.error(f"Không thể tạo TCP server {host}:{port} - {e}")
        raise

def send_udp(packet: dict, mcast_ip: str, mcast_port: int, sock: socket.socket = None, ttl=1):
    """
    Gửi gói UDP / Multicast tới mcast_ip:mcast_port.
    - Nếu không có socket, tự tạo và gửi.
    - TTL chỉ áp dụng cho multicast.
    """
    own_sock = False
    if sock is None:
        sock = create_udp_socket(multicast=True, ttl=ttl)
        own_sock = True
    try:
        addr = (mcast_ip, mcast_port)
        udp_send(sock, packet, addr)
    finally:
        if own_sock:
            sock.close()