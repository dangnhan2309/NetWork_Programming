# server/network.py
# Quản lý TCP server, danh sách clients, và broadcast thông điệp/GAME_STATE.

import socket
import threading
from typing import Dict, Tuple, Optional, Callable
from shared.protocol import encode, decode   # → Hàm mã hoá/giải mã gói tin (newline-delimited)

class ServerNetwork:
    """
    → Lớp server socket:
      - start(): bật server & accept clients
      - broadcast(): gửi packet tới tất cả client
      - send_to(): gửi packet tới 1 client
      - register_state_provider(): đăng ký callback lấy game state (gửi khi JOIN)
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 12345):  # → Khởi tạo server
        self.host = host                     # → Địa chỉ bind
        self.port = port                     # → Cổng lắng nghe
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # → Socket TCP
        self.clients: Dict[socket.socket, Tuple[str, threading.Thread]] = {}  # → Map socket -> (name, thread)
        self.lock = threading.Lock()         # → Khoá bảo vệ self.clients
        self.running = False                 # → Cờ đang chạy
        self._get_state_cb: Optional[Callable[[], dict]] = None  # → Callback lấy game state

    def register_state_provider(self, fn: Callable[[], dict]) -> None:  # → Đăng ký hàm lấy state hiện tại
        self._get_state_cb = fn

    def start(self) -> None:  # → Bật server, listen, tạo thread accept
        self.sock.bind((self.host, self.port))
        self.sock.listen(100)
        self.running = True
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self) -> None:  # → Vòng lặp accept kết nối mới
        while self.running:
            try:
                conn, addr = self.sock.accept()                     # → Client tới
                print(f"[SERVER] Connection from {addr}")
                t = threading.Thread(target=self._client_handler, args=(conn,), daemon=True)  # → Thread xử lý client
                with self.lock:
                    self.clients[conn] = ("<unknown>", t)          # → Tên tạm thời
                t.start()
            except Exception as e:
                if self.running:
                    print("[SERVER] Accept error:", e)

    def _client_handler(self, conn: socket.socket) -> None:  # → Nhận & xử lý gói tin từ 1 client
        try:
            buf = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:                               # → Gói tin kết thúc bằng '\n'
                    line, buf = buf.split(b"\n", 1)
                    pkt = decode(line + b"\n")                    # → Giải mã thành dict
                    if not pkt:
                        continue

                    typ = pkt.get("type")                         # → Phân loại gói tin
                    if typ == "JOIN":                             # → Client gửi JOIN {name}
                        name = pkt.get("name", "anon")
                        with self.lock:
                            self.clients[conn] = (name, self.clients[conn][1])
                        self.broadcast({"type": "CHAT", "name": "SERVER", "message": f"{name} joined."})

                        # → Gửi GAME_STATE riêng cho client vừa JOIN để đồng bộ
                        if self._get_state_cb:
                            try:
                                state = self._get_state_cb()      # → Lấy state hiện tại
                                self.send_to(conn, {"type": "GAME_STATE", "reason": "join_sync", "state": state})
                                print("[SERVER] sent GAME_STATE to", name)
                            except Exception as e:
                                print("[SERVER] get_state error:", e)

                    elif typ == "CHAT":                           # → Relay tin nhắn chat
                        name = self.clients.get(conn, ("<unknown>",))[0]
                        msg = pkt.get("message", "")
                        self.broadcast({"type": "CHAT", "name": name, "message": msg})

                    elif typ == "EXIT":                           # → Client rời đi
                        name = self.clients.get(conn, ("<unknown>",))[0]
                        self.broadcast({"type": "CHAT", "name": "SERVER", "message": f"{name} left."})
                        return
        except Exception as e:
            print("[SERVER] client handler error:", e)
        finally:
            with self.lock:
                if conn in self.clients:
                    del self.clients[conn]                       # → Xoá khỏi danh sách
            try:
                conn.close()
            except:
                pass

    def send_to(self, conn: socket.socket, packet: dict) -> None:  # → Gửi 1 packet tới 1 client
        try:
            conn.sendall(encode(packet))
        except Exception:
            with self.lock:
                if conn in self.clients:
                    del self.clients[conn]

    def broadcast(self, packet: dict) -> None:  # → Gửi 1 packet tới mọi client đang online
        data = encode(packet)
        dead = []
        with self.lock:
            for c in list(self.clients.keys()):
                try:
                    c.sendall(data)
                except Exception:
                    dead.append(c)             # → Gom socket chết để xoá
            for d in dead:
                self.clients.pop(d, None)

    def stop(self) -> None:  # → Tắt server & đóng mọi kết nối
        self.running = False
        with self.lock:
            for c in list(self.clients.keys()):
                try:
                    c.close()
                except:
                    pass
            self.clients.clear()
        try:
            self.sock.close()
        except:
            pass
