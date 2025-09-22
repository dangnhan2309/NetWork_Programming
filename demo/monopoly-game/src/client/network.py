
# src/client/network.py
import socket
import threading
from typing import Callable
from ..shared.protocol import encode,decode
class ClientNetwork:
    def __init__(self, host='127.0.0.1', port=12345, on_message: Callable[[dict], None]=None):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.on_message = on_message
        self.recv_thread = None
        self.running = False

    def connect(self):
        self.sock.connect((self.host, self.port))
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def _recv_loop(self):
        buf = b''
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    pkt = decode(line + b'\n')
                    if pkt and self.on_message:
                        self.on_message(pkt)
            except Exception:
                break
        self.running = False

    def send(self, packet: dict):
        try:
            self.sock.sendall(encode(packet))
        except Exception as e:
            print("[CLIENT] send error:", e)

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except:
            pass
