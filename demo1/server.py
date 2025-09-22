import socket
import threading

HOST = "0.0.0.0"   # Lắng nghe trên tất cả địa chỉ
PORT = 12345

clients = []  # Danh sách client đang kết nối

def broadcast(message, conn):
    """Gửi tin nhắn đến tất cả client trừ người gửi"""
    for client in clients:
        if client != conn:
            try:
                client.sendall(message)
            except:
                client.close()
                clients.remove(client)

def handle_client(conn, addr):
    print(f"[KẾT NỐI] {addr} đã tham gia.")
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break
            print(f"[{addr}] {msg.decode()}")
            broadcast(msg, conn)
        except:
            break
    conn.close()
    clients.remove(conn)
    print(f"[MẤT KẾT NỐI] {addr} đã rời đi.")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Đang lắng nghe tại {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    main()
