# src/server/main.py
import signal
import sys
import threading
from .network import ServerNetwork


def main():
    srv = ServerNetwork(host='0.0.0.0', port=12345)

    # Tạo một Event để kiểm soát việc dừng server
    stop_event = threading.Event()

    def shutdown(sig, frame):
        print("\n[SERVER] Shutting down...")
        # Kích hoạt sự kiện để đánh thức luồng chính
        stop_event.set()
        # Không gọi sys.exit() ở đây, để luồng chính xử lý việc tắt server

    # Đặt trình xử lý cho tín hiệu SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, shutdown)

    # Khởi động server trong một luồng riêng nếu cần
    # Hoặc nếu srv.start() là hàm blocking, chúng ta sẽ để nó ở luồng chính.

    # Giả sử srv.start() là hàm non-blocking
    srv.start()

    print("[SERVER] Server started. Press Ctrl+C to shut down.")

    # Luồng chính sẽ tạm dừng và chờ cho đến khi sự kiện được thiết lập
    stop_event.wait()

    # Sau khi sự kiện được kích hoạt, luồng chính sẽ tiếp tục
    srv.stop()
    print("[SERVER] Server stopped.")
    sys.exit(0)


if __name__ == '__main__':
    main()