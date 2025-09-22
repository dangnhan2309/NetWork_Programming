import socket
import threading
import json
import random

class Player:
    def __init__(self, name, conn):
        self.name = name
        self.money = 1500
        self.position = 0
        self.conn = conn

class MonopolyServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.players = []
        self.current_turn = 0
        self.lock = threading.Lock()

    def broadcast(self, msg):
        data = json.dumps(msg).encode()
        for p in self.players:
            p.conn.sendall(data + b"\n")

    def handle_client(self, conn, addr):
        name = conn.recv(1024).decode().strip()
        player = Player(name, conn)
        self.players.append(player)
        self.broadcast({"msg": f"{name} đã tham gia game!"})

        while True:
            data = conn.recv(1024)
            if not data: break
            msg = json.loads(data.decode())
            if msg["action"] == "roll":
                self.play_turn(player)

    def play_turn(self, player):
        with self.lock:
            dice = random.randint(1, 6) + random.randint(1, 6)
            player.position = (player.position + dice) % 10
            self.broadcast({
                "msg": f"{player.name} gieo được {dice}, đến ô {player.position}"
            })
            # TODO: xử lý mua đất, trả tiền, thuế...

    def start(self):
        print("Server Monopoly chạy...")
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

MonopolyServer().start()
