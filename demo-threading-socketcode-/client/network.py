# client/network.py
# Kết nối TCP tới server, nhận/gửi packet, xử lý built-in (CHAT/GAME_STATE) và render ASCII board.

import socket
import threading
import sys
from typing import Callable, Optional
from shared.protocol import encode, decode

# → Cố gắng set UTF-8 để in tiếng Việt ổn trên Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def _safe_print(s: str) -> None:  # → In an toàn, tránh UnicodeEncodeError
    try:
        print(s)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((s + "\n").encode(sys.stdout.encoding or "utf-8", errors="ignore"))
        except Exception:
            print(s.encode("ascii", errors="ignore").decode("ascii"))

class ClientNetwork:
    """
    → Client TCP:
      - connect(): nối tới server + chạy thread nhận
      - send(): gửi packet
      - _recv_loop(): nhận theo newline, decode & dispatch
      - _handle_builtin(): xử lý CHAT/GAME_STATE
      - _try_render_ascii(): gọi server.board.Board để vẽ bản đồ ASCII
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 12345, on_message: Optional[Callable[[dict], None]] = None):
        self.host = host                                  # → Địa chỉ server
        self.port = port                                  # → Cổng server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.on_message = on_message                      # → Callback custom (nếu cần)
        self.recv_thread: Optional[threading.Thread] = None
        self.running = False

    def connect(self) -> None:                            # → Kết nối & start thread nhận
        self.sock.connect((self.host, self.port))
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def _recv_loop(self) -> None:                         # → Nhận dữ liệu & tách gói theo '\n'
        buf = b""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    pkt = decode(line + b"\n")
                    if not pkt:
                        continue

                    handled = self._handle_builtin(pkt)   # → Ưu tiên xử lý builtin

                    if not handled and self.on_message:   # → Chỉ gọi callback nếu chưa handled để tránh in trùng
                        try:
                            self.on_message(pkt)
                        except Exception as e:
                            _safe_print(f"[CLIENT] on_message error: {e}")

                    if not handled and not self.on_message:   # → Không có callback: in thô
                        _safe_print(f"[CLIENT] pkt: {pkt}")

            except Exception as e:
                _safe_print(f"[CLIENT] recv error: {e}")
                break
        self.running = False

    def _handle_builtin(self, pkt: dict) -> bool:        # → Xử lý gói builtin; trả True nếu đã xử lý
        ptype = pkt.get("type")

        if ptype == "GAME_STATE":                         # → Gói state: in & thử vẽ bản đồ
            reason = pkt.get("reason", "")
            state = pkt.get("state", {})
            _safe_print(f"===> Received GAME_STATE ({reason})")
            if state:
                if self._try_render_ascii(state):
                    return True
                else:
                    _safe_print(f"[CLIENT] (raw state) {state}")
            return True

        if ptype == "CHAT":                               # → Gói chat: hiển thị “\[name] message”
            name = pkt.get("name", "??")
            msg = pkt.get("message", "")
            _safe_print(f"[{name}] {msg}")
            return True

        if ptype == "ERROR":                              # → Gói lỗi từ server
            _safe_print(f"[SERVER ERROR] {pkt.get('message','')}")
            return True

        return False

    def _try_render_ascii(self, state: dict) -> bool:     # → Render ASCII bằng server.board.Board
        try:
            from server.board import Board                 # → Import Board từ package server
        except Exception as e:
            _safe_print(f"[CLIENT] Không import được Board từ server.board: {e}")
            return False

        try:
            board = Board()
            ascii_map = board.render_ascii(state)         # → Board.render_ascii(state) trả chuỗi nhiều dòng
            for line in ascii_map.splitlines():
                _safe_print(line)
            return True
        except Exception as e:
            _safe_print(f"[CLIENT] Lỗi render ASCII: {e}")
            return False

    def send(self, packet: dict) -> None:                # → Gửi packet lên server
        try:
            self.sock.sendall(encode(packet))
        except Exception as e:
            _safe_print(f"[CLIENT] send error: {e}")

    def send_join(self, name: str) -> None:              # → Tiện: gửi JOIN nhanh
        self.send({"type": "JOIN", "name": name})

    def close(self) -> None:                             # → Đóng kết nối
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass
        if self.recv_thread and self.recv_thread.is_alive():
            self.recv_thread.join(timeout=1)  # → Chờ thread nhận kết thúc