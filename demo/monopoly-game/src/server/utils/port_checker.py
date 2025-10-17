# src/utils/port_checker.py
import socket
import random
import threading
from typing import List, Optional

# Import logger đúng path ( điều chỉnh theo project của bạn )
try:
    # Nếu package layout là src.utils.logger
    from ..utils.logger import Logger

# 🚨 CATCH LỖI IMPORT CỤ THỂ 🚨
except ImportError:
    # Fallback nếu import khác (gói không tồn tại hoặc đường dẫn sai)
    class Logger:
        def __init__(self, name=None): self.name = name

        def info(self, m): print(f"[{self.name}][INFO] {m}")

        def success(self, m): print(f"[{self.name}][SUCCESS] {m}")

        def error(self, m): print(f"[{self.name}][ERROR] {m}")
class PortChecker:
    """
    Kiểm tra và quản lý cổng UDP khả dụng cho multicast.
    """

    def __init__(self, start_port: int = 5000, end_port: int = 6000):
        self.start_port = start_port
        self.end_port = end_port
        self.available_ports: List[int] = []
        self.logger = Logger("PortChecker")
        self.lock = threading.Lock()

    def is_port_available(self, port: int) -> bool:
        """Kiểm tra xem port có đang rảnh để dùng không (UDP)."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", port))
            sock.close()
            return True
        except OSError:
            return False

    def scan_ports(self) -> None:
        """Quét và lưu danh sách các cổng khả dụng."""
        self.logger.info(f"Scanning ports {self.start_port}–{self.end_port}...")
        with self.lock:
            self.available_ports.clear()
            for port in range(self.start_port, self.end_port + 1):
                if self.is_port_available(port):
                    self.available_ports.append(port)
        self.logger.success(f"Found {len(self.available_ports)} available ports.")

    def get_random_port(self) -> Optional[int]:
        """Lấy ngẫu nhiên 1 port từ danh sách khả dụng — trả None nếu không còn."""
        with self.lock:
            if not self.available_ports:
                self.scan_ports()
            if self.available_ports:
                port = random.choice(self.available_ports)
                # Reserve (remove) port từ pool để tránh trùng
                self.available_ports.remove(port)
                self.logger.info(f"Selected port {port}")
                return port
            else:
                self.logger.error("No available ports found!")
                return None

    def release_port(self, port: int) -> None:
        """Giải phóng port để dùng lại."""
        with self.lock:
            if port not in self.available_ports:
                self.available_ports.append(port)
                self.logger.info(f"Released port {port} back to pool.")

    def list_ports(self) -> List[int]:
        """Trả về danh sách port hiện còn khả dụng."""
        with self.lock:
            return list(self.available_ports)
