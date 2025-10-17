"""
Network Utilities Module - Complete Version
-------------------------------------------
Hỗ trợ gửi / nhận gói tin mạng (TCP, UDP, Multicast) theo chuẩn packet_format
Tích hợp PortChecker và đầy đủ chức năng
"""

import socket
import struct
import json
from typing import Tuple, Optional, Dict, Any
from .packet_format import PacketFormat
from .logger import Logger
from .port_checker import PortChecker

logger = Logger("network_utils")

# ======================================================
# 🌐 GLOBAL PORT CHECKER (chỉ quét 1 lần duy nhất)
# ======================================================
PORT_CHECKER = None

def _init_port_checker():
    """Khởi tạo PortChecker nếu chưa có"""
    global PORT_CHECKER
    if PORT_CHECKER is None:
        PORT_CHECKER = PortChecker(5000, 6000)
        PORT_CHECKER.scan_ports()

# ============================================================
# 🧱 CORE ENCODE / DECODE LAYER
# ============================================================
def encode_packet(packet: dict) -> bytes:
    """Encode packet theo chuẩn utils.packet_format, fallback sang JSON"""
    try:
        return PacketFormat.encode_packet(packet) 
    except Exception as e:
        logger.warning(f"Packet format encode lỗi ({e}), fallback sang JSON.")
        try:
            return json.dumps(packet).encode("utf-8")
        except Exception as e2:
            logger.error(f"Encode JSON thất bại: {e2}")
            return b""

def decode_packet(data: bytes) -> dict | None:
    """Decode packet, fallback JSON nếu cần"""
    try:
        return PacketFormat.decode_packet(data)
    except Exception:
        try:
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Decode packet lỗi ({e}), bỏ qua.")
            return None

# ============================================================
# ⚙️ VALIDATION & LOGGING
# ============================================================
def validate_packet(packet: dict) -> bool:
    """Kiểm tra packet hợp lệ"""
    if PacketFormat.is_valid(packet):
        return True
    # Fallback validation cho packet cũ
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
    pkt_type = packet.get("header", {}).get("type", packet.get("type", "unknown"))
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
        if packet and validate_packet(packet):
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
    """Gửi packet qua UDP hoặc Multicast"""
    try:
        encoded = encode_packet(packet)
        sock.sendto(encoded, addr)
        log_packet(packet, "SEND-UDP")
    except Exception as e:
        logger.error(f"Lỗi UDP send tới {addr}: {e}")

def udp_receive(sock: socket.socket, buffer_size=4096) -> tuple[dict | None, tuple | None]:
    """Nhận packet từ UDP hoặc Multicast"""
    try:
        data, addr = sock.recvfrom(buffer_size)
        packet = decode_packet(data)
        if packet and validate_packet(packet):
            log_packet(packet, "RECV-UDP")
            return packet, addr
        logger.warning(f"Gói tin không hợp lệ từ {addr}")
        return None, addr
    except Exception as e:
        logger.error(f"Lỗi UDP receive: {e}")
        return None, None

# ======================================================
# 🧩 UDP SOCKET CREATION (Improved)
# ======================================================
def create_udp_socket(multicast: bool = False, port: int = 0, reuse: bool = True, ttl: int = 2) -> socket.socket:
    """Tạo UDP socket và tự động chọn port khả dụng"""
    _init_port_checker()
    
    # Nếu chưa có port được chỉ định, chọn ngẫu nhiên từ danh sách khả dụng
    if port == 0:
        port = PORT_CHECKER.get_random_port()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    
    if reuse:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    if multicast:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        sock.bind(('', port))
        logger.info(f"[UDP SOCKET] ✅ Bound to port {port}")
    except Exception as e:
        logger.error(f"[UDP SOCKET] ❌ Failed to bind port {port}: {e}")
        raise e

    return sock

# ======================================================
# 📡 MULTICAST JOIN / LEAVE
# ======================================================
def join_multicast_group(sock: socket.socket, multicast_ip: str) -> bool:
    """Tham gia multicast group"""
    try:
        mreq = struct.pack("4sl", socket.inet_aton(multicast_ip), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        logger.info(f"[MULTICAST] ✅ Joined group {multicast_ip}")
        return True
    except Exception as e:
        logger.error(f"[MULTICAST] ❌ Error joining {multicast_ip}: {e}")
        return False

def leave_multicast_group(sock: socket.socket, multicast_ip: str) -> bool:
    """Rời khỏi multicast group"""
    try:
        mreq = struct.pack("4sl", socket.inet_aton(multicast_ip), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
        logger.info(f"[MULTICAST] ✅ Left group {multicast_ip}")
        return True
    except Exception as e:
        logger.error(f"[MULTICAST] ❌ Error leaving {multicast_ip}: {e}")
        return False

# ============================================================
# 🧠 HIGH-LEVEL HELPERS
# ============================================================
def send(sock: socket.socket, packet: dict, addr=None, protocol="auto"):
    """Hàm gửi linh hoạt: TCP hoặc UDP"""
    if protocol == "tcp" or (protocol == "auto" and sock.type == socket.SOCK_STREAM):
        tcp_send(sock, packet)
    else:
        if addr is None:
            raise ValueError("UDP cần địa chỉ đích (addr)")
        udp_send(sock, packet, addr)

def receive(sock: socket.socket, protocol="auto", buffer_size=4096):
    """Hàm nhận linh hoạt: TCP hoặc UDP"""
    if protocol == "tcp" or (protocol == "auto" and sock.type == socket.SOCK_STREAM):
        return tcp_receive(sock, buffer_size)
    else:
        return udp_receive(sock, buffer_size)

# ============================================================
# 🔍 UTILITIES
# ============================================================
def create_tcp_server(host: str, port: int, backlog=5) -> socket.socket:
    """Tạo TCP server socket, bind và listen"""
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

def send_udp_basic(packet: dict, mcast_ip: str, mcast_port: int, sock: socket.socket = None, ttl=1):
    """Gửi gói UDP / Multicast (basic version - không encode packetformat)"""
    own_sock = False
    if sock is None:
        sock = create_udp_socket(multicast=True, ttl=ttl)
        own_sock = True
    try:
        addr = (mcast_ip, mcast_port)
        # Sử dụng encode cơ bản cho JSON
        encoded = json.dumps(packet).encode('utf-8')
        sock.sendto(encoded, addr)
        logger.info(f"[UDP BASIC] Sent to {mcast_ip}:{mcast_port}")
    finally:
        if own_sock:
            sock.close()

def get_available_port(start_port: int = 5000, end_port: int = 6000) -> int:
    """Lấy port khả dụng"""
    _init_port_checker()
    return PORT_CHECKER.get_random_port()

def get_local_ip() -> str:
    """Lấy local IP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def safe_udp_receive(sock: socket.socket):
    """Nhận UDP data an toàn cho non-blocking sockets"""
    try:
        data, addr = sock.recvfrom(65535)
        if data:
            try:
                # Thử decode với PacketFormat
                packet = PacketFormat.decode_packet(data)
                logger.debug(f"[RECV-UDP] {packet.get('header', {}).get('type', 'unknown')} from {addr}")
                return packet, addr
            except Exception as decode_error:
                # Fallback to JSON
                try:
                    packet_str = data.decode('utf-8')
                    packet = json.loads(packet_str)
                    logger.debug(f"[RECV-UDP-FALLBACK] JSON from {addr}")
                    return packet, addr
                except Exception as json_error:
                    logger.error(f"Lỗi decode UDP packet: {decode_error}, JSON: {json_error}")
                    return None, addr
        return None, None
    except BlockingIOError:
        # No data available - normal case
        return None, None
    except Exception as e:
        logger.error(f"Lỗi UDP receive: {e}")
        return None, None