 
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

<<<<<<< Updated upstream
    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(100)
        self.running = True
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()
=======
    async def handler(self, websocket):
        """Xử lý kết nối từ client"""
        player_name = None
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    cmd = data.get("cmd")
                    payload = data.get("data", {})
                    
                    if cmd == "join":
                        name = payload.get("name", "Unknown")
                        if self.game_manager.add_player(name, websocket):
                            player_name = name
                            self.clients[websocket] = name
                            await self.send(websocket, "info", f"Welcome {name}! Waiting for game to start...")
                            await self.send(websocket, "game_state", self.game_manager.get_game_state())
                        else:
                            await self.send(websocket, "error", "Cannot join game (game full or name taken)")
                            
                    elif cmd == "roll":
                        if player_name:
                            result = self.game_manager.handle_player_action(player_name, "ROLL")
                            await self.send(websocket, "action_result", result)
                        else:
                            await self.send(websocket, "error", "You must join game first")
                            
                    elif cmd == "buy":
                        if player_name:
                            result = self.game_manager.handle_player_action(player_name, "BUY")
                            await self.send(websocket, "action_result", result)
                        else:
                            await self.send(websocket, "error", "You must join game first")
                            
                    elif cmd == "end_turn":
                        if player_name:
                            result = self.game_manager.handle_player_action(player_name, "END_TURN")
                            await self.send(websocket, "action_result", result)
                        else:
                            await self.send(websocket, "error", "You must join game first")
                            
                    elif cmd == "state":  # THÊM XỬ LÝ LỆNH STATE
                        await self.send(websocket, "game_state", self.game_manager.get_game_state())
                        
                    elif cmd == "help":
                        help_text = (
                            "📖 DANH SÁCH LỆNH:\n"
                            "/join <tên>    - Tham gia game\n"
                            "/roll          - Đổ xúc xắc\n" 
                            "/buy           - Mua đất\n"
                            "/end_turn      - Kết thúc lượt\n"
                            "/state         - Xem trạng thái game\n"
                            "/help          - Xem trợ giúp\n"
                            "/quit          - Thoát game\n"
                        )
                        await self.send(websocket, "info", help_text)
                        
                    elif cmd == "quit":
                        break
                        
                    else:
                        await self.send(websocket, "error", f"Unknown command: {cmd}")
                        
                except json.JSONDecodeError:
                    await self.send(websocket, "error", "Invalid JSON format")
                except Exception as e:
                    await self.send(websocket, "error", f"Server error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Connection closed for {player_name}")
        finally:
            # Cleanup khi client disconnect
            if player_name:
                self.game_manager.remove_player(player_name)
            if websocket in self.clients:
                del self.clients[websocket]
            await self.broadcast_state()
>>>>>>> Stashed changes

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
