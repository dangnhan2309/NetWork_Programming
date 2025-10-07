import socket
import random
import threading
from ..utils import logger as Logger

class PortChecker:
    """
    Kiểm tra và quản lý cổng UDP khả dụng cho multicast.
    Có thể dùng cả ở client và server.
    Example :
    from utils.port_checker import PortChecker

    if __name__ == "__main__":
        checker = PortChecker(5500, 5550)

        checker.scan_ports()
        print("Available ports:", checker.list_ports())

        port = checker.get_random_port()
        print("Chosen port:", port)

        checker.release_port(port)
        print("Ports after release:", checker.list_ports())

    Result :
    [INFO] [PortChecker] Scanning ports 5500–5550...
    [SUCCESS] [PortChecker] Found 23 available ports.
    [INFO] [PortChecker] Selected port 5521
    [INFO] [PortChecker] Released port 5521 back to pool.


    """

    def __init__(self, start_port=5000, end_port=6000):
        self.start_port = start_port
        self.end_port = end_port
        self.available_ports = []
        self.logger = Logger("PortChecker")
        self.lock = threading.Lock()

    # ==================================================
    def is_port_available(self, port: int) -> bool:
        """Kiểm tra xem port có đang rảnh để dùng không."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("", port))
            sock.close()
            return True
        except OSError:
            return False

    # ==================================================
    def scan_ports(self):
        """Quét và lưu danh sách các cổng khả dụng."""
        self.logger.info(f"Scanning ports {self.start_port}–{self.end_port}...")
        with self.lock:
            self.available_ports.clear()
            for port in range(self.start_port, self.end_port + 1):
                if self.is_port_available(port):
                    self.available_ports.append(port)
        self.logger.success(f"Found {len(self.available_ports)} available ports.")

    # ==================================================
    def get_random_port(self) -> int:
        """Lấy ngẫu nhiên 1 port từ danh sách khả dụng."""
        with self.lock:
            if not self.available_ports:
                self.scan_ports()
            if self.available_ports:
                port = random.choice(self.available_ports)
                self.available_ports.remove(port)
                self.logger.info(f"Selected port {port}")
                return port
            else:
                self.logger.error("No available ports found!")
                return None

    # ==================================================
    def release_port(self, port: int):
        """Giải phóng port để dùng lại."""
        with self.lock:
            if port not in self.available_ports:
                self.available_ports.append(port)
                self.logger.info(f"Released port {port} back to pool.")

    # ==================================================
    def list_ports(self):
        """Trả về danh sách port hiện còn khả dụng."""
        with self.lock:
            return list(self.available_ports)
