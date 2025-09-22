import socket
import threading
import json

def listen(server):
    while True:
        data = server.recv(1024).decode()
        if not data: break
        for line in data.strip().split("\n"):
            msg = json.loads(line)
            print("📢", msg["msg"])

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 5555))

    name = input("Nhập tên của bạn: ")
    s.sendall(name.encode())

    threading.Thread(target=listen, args=(s,), daemon=True).start()

    while True:
        cmd = input("Nhập lệnh (roll/mua/thóat): ")
        if cmd == "roll":
            s.sendall(json.dumps({"action": "roll"}).encode())
        elif cmd == "quit":
            break

main()
