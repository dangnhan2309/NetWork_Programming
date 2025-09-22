import socket
import threading

SERVER_IP = "127.0.0.1"   # Đổi sang IP của server nếu khác máy
PORT = 12345

def receive_messages(client):
    """Luồng nhận tin nhắn"""
    while True:
        try:
            msg = client.recv(1024).decode()
            if msg:
                print("\n" + msg)
        except:
            print("[LỖI] Mất kết nối đến server.")
            client.close()
            break

def send_messages(client):
    """Luồng gửi tin nhắn"""
    while True:
        msg = input("")
        client.sendall(msg.encode())

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    print("[CLIENT] Kết nối thành công!")

    # Chạy 2 luồng song song
    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()
    send_messages(client)

if __name__ == "__main__":
    main()
