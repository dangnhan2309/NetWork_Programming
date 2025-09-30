# server/main.py
# Entry point: khởi động ServerNetwork + GameManager, đăng ký state provider, game loop & shutdown an toàn.

import signal
import sys
import threading
import time

from .network import ServerNetwork   # → TCP server/broadcast
from .game_manager import GameManager
from .player import Player

def main():  # → Hàm chạy server
    srv = ServerNetwork(host="0.0.0.0", port=12345)   # → Khởi tạo server socket

    players = [Player("A"), Player("B")]              # → Tạo 2 người chơi demo
    gm = GameManager(players=players, network=srv)    # → GM có tham chiếu server để broadcast

    srv.register_state_provider(gm.get_state)         # → Gửi GAME_STATE ngay khi client JOIN

    stop_event = threading.Event()                    # → Đồng bộ tín hiệu tắt

    def shutdown(sig, frame):                         # → Handler Ctrl+C
        print("\n[SERVER] Shutting down...")
        stop_event.set()

    signal.signal(signal.SIGINT, shutdown)            # → Đăng ký Ctrl+C

    srv.start()                                       # → Bật server (non-blocking)
    print("[SERVER] Server started. Press Ctrl+C to shut down.")

    def game_loop():                                   # → Vòng game demo: mỗi 3s chạy 1 lượt
        while not stop_event.is_set():
            gm.play_turn()                             # → Lượt sẽ tự sync_state() bên trong
            time.sleep(3)

    threading.Thread(target=game_loop, daemon=True).start()  # → Chạy game loop nền

    stop_event.wait()                                  # → Đợi Ctrl+C
    srv.stop()                                         # → Đóng server/clients
    print("[SERVER] Server stopped.")
    sys.exit(0)                                        # → Thoát

if __name__ == "__main__":
    main()  # → Chạy entry
# server/board.py
# Logic bàn cờ & vẽ board ASCII dựa trên state (dùng trong server/game_manager.py để tạo GAME_STATE).