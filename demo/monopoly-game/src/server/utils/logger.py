import json
import os
import datetime
import threading
import inspect

class Logger:
    """
    Logger hỗ trợ:
      - Ghi log ra console với màu sắc theo cấp độ.
      - Ghi log vào file JSON và TXT.
      - Thread-safe: hỗ trợ nhiều luồng.
      - Debug: in thêm thông tin caller, thread.
    """

    LOG_DIR = "logs"

    COLOR_MAP = {
        "DEBUG": "\033[96m",    # Cyan nhạt
        "INFO": "\033[94m",     # Xanh dương
        "SUCCESS": "\033[92m",  # Xanh lá
        "WARNING": "\033[93m",  # Vàng
        "ERROR": "\033[91m",    # Đỏ
        "RESET": "\033[0m"      # Reset màu
    }

    def __init__(self, room_id=None):
        self.room_id = room_id
        os.makedirs(self.LOG_DIR, exist_ok=True)
        self.log_file = os.path.join(self.LOG_DIR, f"{room_id or 'server'}.log.json")
        self.log_txt_file = os.path.join(self.LOG_DIR, f"{room_id or 'server'}.log.txt")
        self.lock = threading.Lock()

    def _get_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_to_file(self, entry: dict):
        """Ghi log ra file JSON và TXT"""
        with self.lock:
            # JSON
            with open(self.log_file, "a", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False)
                f.write("\n")
            # TXT
            with open(self.log_txt_file, "a", encoding="utf-8") as f:
                ts = entry.get("timestamp")
                level = entry.get("level")
                msg = entry.get("message")
                f.write(f"[{ts}] [{level}] [{self.room_id or 'GLOBAL'}] {msg}\n")

    def _print_to_console(self, level: str, message: str):
        color = self.COLOR_MAP.get(level, "")
        reset = self.COLOR_MAP["RESET"]
        print(f"{color}[{level}] {message}{reset}")

    def log(self, level: str, message: str, **extra):
        entry = {
            "timestamp": self._get_timestamp(),
            "level": level,
            "room_id": self.room_id,
            "message": message,
            **extra
        }
        self._print_to_console(level, f"[{self.room_id or 'GLOBAL'}] {message}")
        self._write_to_file(entry)

    # ===== Shortcut Methods =====
    def debug(self, message, **extra):
        caller = inspect.stack()[1].function
        thread_name = threading.current_thread().name
        full_message = f"{message} (Thread: {thread_name}, Func: {caller})"
        self.log("DEBUG", full_message, **extra)

    def info(self, message, **extra):
        self.log("INFO", message, **extra)

    def success(self, message, **extra):
        self.log("SUCCESS", message, **extra)

    def warning(self, message, **extra):
        self.log("WARNING", message, **extra)

    def error(self, message, **extra):
        self.log("ERROR", message, **extra)
    def log_packet(self, direction: str, addr: tuple, packet: dict):
        """
        Ghi log packet gửi/nhận.
        direction: "SEND" hoặc "RECV"
        addr: địa chỉ IP:port
        packet: dict packet
        """
        try:
            # Chuyển packet thành string gọn gàng (JSON pretty)
            packet_str = json.dumps(packet, ensure_ascii=False, indent=2)
            message = f"[{direction}] {addr}\n{packet_str}"
            self.debug(message)
        except Exception as e:
            self.error(f"Failed to log packet: {e}")
