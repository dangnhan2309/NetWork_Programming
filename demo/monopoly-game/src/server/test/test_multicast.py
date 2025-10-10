# tests/test_multicast.py
"""
Test multicast UDP với GameManager
- Khởi tạo 1 phòng, thêm 2 player
- Gửi STATE_UPDATE qua multicast
- Receiver lắng nghe và in packet nhận được
"""

import threading
import time
from ..network import network_utils as net
from ..game import GameManager

ROOM_ID = "TEST_ROOM"
MULTICAST_IP = "239.0.0.1"
MULTICAST_PORT = 6000
TTL = 2

def multicast_receiver():
    """Thread nhận packet multicast"""
    sock = net.create_udp_socket(multicast=True, ttl=TTL)
    sock.bind(("", MULTICAST_PORT))
    net.join_multicast_group(sock, MULTICAST_IP)

    print("[Receiver] Waiting for STATE_UPDATE packet...")
    packet, addr = net.udp_receive(sock)
    if packet:
        print(f"[Receiver] Received packet from {addr}: {packet}")
    else:
        print("[Receiver] No valid packet received.")

    net.leave_multicast_group(sock, MULTICAST_IP)
    sock.close()

def test_game_multicast():
    """Tạo game, gửi STATE_UPDATE qua multicast"""
    # Khởi tạo GameManager
    game = GameManager(room_id=ROOM_ID)
    game.add_player("player1", "Alice")
    game.add_player("player2", "Bob")
    game.start_game()

    # Tạo thread receiver
    recv_thread = threading.Thread(target=multicast_receiver, daemon=True)
    recv_thread.start()

    # Chờ 1s để receiver sẵn sàng
    time.sleep(1)

    # Xây dựng packet STATE_UPDATE
    state_packet = game.build_state_packet()
    addr = (MULTICAST_IP, MULTICAST_PORT)

    print(f"[Sender] Sending STATE_UPDATE to {addr}")
    sock = net.create_udp_socket(multicast=True, ttl=TTL)
    net.udp_send(sock, state_packet, addr)
    sock.close()

    # Chờ receiver xử lý
    recv_thread.join()
    print("[Test] GameManager multicast STATE_UPDATE test completed.")

if __name__ == "__main__":
    test_game_multicast()
