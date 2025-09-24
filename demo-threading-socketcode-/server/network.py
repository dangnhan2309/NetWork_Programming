 
# src/server/network.py
import socket
import threading
from typing import Callable, Dict, Tuple, List
from ..shared.protocol import encode, decode

class ServerNetwork:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: Dict[socket.socket, Tuple[str, threading.Thread]] = {}
        self.lock = threading.Lock()
        self.running = False

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(100)
        self.running = True
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()

    def _accept_loop(self):
        while self.running:
            try:
                conn, addr = self.sock.accept()
                print(f"[SERVER] Connection from {addr}")
                t = threading.Thread(target=self._client_handler, args=(conn,), daemon=True)
                with self.lock:
                    self.clients[conn] = ("<unknown>", t)
                t.start()
            except Exception as e:
                print("[SERVER] Accept error:", e)

    def _client_handler(self, conn: socket.socket):
        try:
            buf = b''
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    pkt = decode(line + b'\n')
                    if not pkt:
                        continue
                    ptype = pkt.get('type')
                    if ptype == 'JOIN':
                        name = pkt.get('name', 'anon')
                        with self.lock:
                            self.clients[conn] = (name, self.clients[conn][1])
                        self.broadcast({'type':'CHAT', 'name':'SERVER', 'message': f"{name} joined."})
                    elif ptype == 'CHAT':
                        name = self.clients.get(conn, ("<unknown>",))[0]
                        message = pkt.get('message', '')
                        self.broadcast({'type':'CHAT', 'name': name, 'message': message})
                    elif ptype == 'EXIT':
                        name = self.clients.get(conn, ("<unknown>",))[0]
                        self.broadcast({'type':'CHAT', 'name':'SERVER', 'message': f"{name} left."})
                        conn.close()
                        return
        except Exception as e:
            print("[SERVER] client handler error:", e)
        finally:
            with self.lock:
                if conn in self.clients:
                    del self.clients[conn]
            try:
                conn.close()
            except:
                pass

    def broadcast(self, packet: dict):
        data = encode(packet)
        dead = []
        with self.lock:
            for c in list(self.clients.keys()):
                try:
                    c.sendall(data)
                except Exception:
                    dead.append(c)
            for d in dead:
                del self.clients[d]

    def stop(self):
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
