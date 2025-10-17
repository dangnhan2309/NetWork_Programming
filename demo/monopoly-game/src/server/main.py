import asyncio
import signal
import sys
from .config.server_config import SERVER_CONFIG
from .rooms.room_manager import RoomManager
from .game.game_manager import GameManager
from .network.tcp_handler import TCPHandler
from .network.udp_multicast import UDPHandler
from .network.multiplecast_manager import MulticastManager
from .utils.logger import Logger
from .utils.formatters import ServerFormatter


class MonopolyServer:
    """Server chính cho game Monopoly"""

    def __init__(self):
        self.running = [True]
        self.logger = Logger("Server")
        self.formatter = ServerFormatter()
        self.room_manager = None
        self.game_manager = None
        self.tcp_handler = None
        self.udp_handler = None
        self.multicast_manager = None

    async def initialize(self):
        """Khởi tạo server"""
        self.logger.info("🚀 Đang khởi động Monopoly Server...")
        try:
            # 1. Khởi tạo MulticastManager
            self.logger.info("🔧 Khởi tạo MulticastManager...")
            self.multicast_manager = MulticastManager()

            # 2. Khởi tạo RoomManager
            self.logger.info("🏠 Khởi tạo RoomManager...")
            self.room_manager = RoomManager(self.logger)

            # 3. Khởi tạo GameManager
            self.logger.info("🎮 Khởi tạo GameManager...")
            self.game_manager = GameManager(self.logger)

            # 4. Inject MulticastManager
            if hasattr(self.game_manager, "set_multicast_manager"):
                self.game_manager.set_multicast_manager(self.multicast_manager)
                self.logger.info("✅ Đã inject multicast manager vào GameManager")

            # 5. Khởi tạo TCP & UDP
            self.logger.info("📡 Khởi tạo TCPHandler...")
            self.tcp_handler = TCPHandler(
                self.room_manager, self.game_manager, self.logger, self.multicast_manager
            )

            self.logger.info("🌐 Khởi tạo UDPHandler...")
            self.udp_handler = UDPHandler(
                self.room_manager, self.logger, self.multicast_manager
            )

            # 6. Thiết lập callback broadcast
            if hasattr(self.udp_handler, "broadcast_system_message"):
                self.logger.info("🔄 Thiết lập broadcast callback...")
                self.tcp_handler.set_broadcast_callback(
                    self.udp_handler.broadcast_system_message
                )

            self.logger.info("✅ Server đã được khởi tạo thành công")
        except Exception as e:
            self.logger.error(f"❌ Lỗi khởi tạo server: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise

    async def run(self):
        """Chạy server chính"""
        await self.initialize()

        # Đăng ký signal handler
        loop = asyncio.get_running_loop()
        try:
            loop.add_signal_handler(signal.SIGINT, self.signal_handler, None, None)
            loop.add_signal_handler(signal.SIGTERM, self.signal_handler, None, None)
        except NotImplementedError:
            # Windows không hỗ trợ add_signal_handler
            import threading
            threading.Thread(target=self._windows_signal_monitor, daemon=True).start()

        tcp_host = SERVER_CONFIG.tcp_host
        tcp_port = SERVER_CONFIG.tcp_port
        udp_task = None
        main_loop_task = None

        try:
            # Khởi động TCP server
            self.logger.info(f"🔄 Đang khởi động TCP server trên {tcp_host}:{tcp_port}")
            server = await asyncio.start_server(
                self.tcp_handler.handle_client, tcp_host, tcp_port
            )

            # Chạy UDP handler (không có tham số)
            self.logger.info("📡 Khởi động UDP handler...")
            udp_task = asyncio.create_task(self.udp_handler.run(), name="UDPHandler")

            # Chạy vòng lặp chính
            main_loop_task = asyncio.create_task(self.main_loop(), name="MainLoop")

            # Hiển thị thông tin
            self.display_server_info()

            async with server:
                await server.serve_forever()
        except Exception as e:
            self.logger.error(f"❌ Khởi động server thất bại: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            if self.udp_handler:
                self.udp_handler.stop()
            await self.shutdown([udp_task, main_loop_task])

    async def main_loop(self):
        """Vòng lặp chính của server"""
        self.logger.info("🌀 Vòng lặp chính đã bắt đầu")
        last_udp_process = 0
        last_heartbeat = 0
        last_status_display = 0

        while self.running[0]:
            try:
                now = asyncio.get_event_loop().time()

                # Xử lý UDP
                if now - last_udp_process >= 1.0:
                    if hasattr(self.udp_handler, "process_udp_messages"):
                        await self.udp_handler.process_udp_messages()
                    last_udp_process = now

                # Gửi heartbeat
                if now - last_heartbeat >= 30:
                    if hasattr(self.udp_handler, "send_heartbeats"):
                        await self.udp_handler.send_heartbeats()
                    last_heartbeat = now

                # Hiển thị status
                if now - last_status_display >= 30:
                    await self.display_server_status()
                    last_status_display = now

                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"❌ Lỗi vòng lặp chính: {e}")
                await asyncio.sleep(2)

        self.logger.info("🧩 Vòng lặp chính đã dừng")

    async def display_server_status(self):
        """Hiển thị trạng thái server"""
        try:
            rooms_count = len(self.room_manager.rooms)
            players_count = sum(
                len(room["players"]) for room in self.room_manager.rooms.values()
            )
            clients_count = (
                len(self.tcp_handler.connected_clients)
                if hasattr(self.tcp_handler, "connected_clients")
                else 0
            )

            multicast_info = ""
            if self.multicast_manager and hasattr(self.multicast_manager, "groups"):
                multicast_rooms = len(self.multicast_manager.groups)
                active_rooms = []
                for room_id, group_info in self.multicast_manager.groups.items():
                    if group_info and isinstance(group_info, dict):
                        ip = group_info.get("ip", "N/A")
                        port = group_info.get("port", "N/A")
                        active_rooms.append(f"{room_id}({ip}:{port})")
                multicast_info = f" | Multicast: {multicast_rooms} phòng"
                if active_rooms:
                    multicast_info += f" [{', '.join(active_rooms[:2])}{'...' if len(active_rooms) > 2 else ''}]"
            else:
                multicast_info = " | Multicast: Not available"

            status_msg = f"📊 SERVER STATUS | Phòng: {rooms_count} | Người chơi: {players_count} | Client: {clients_count}{multicast_info}"
            self.logger.info(status_msg)
        except Exception as e:
            self.logger.error(f"❌ Lỗi hiển thị status: {e}")

    def display_server_info(self):
        """Hiển thị thông tin server"""
        print("\n" + "=" * 60)
        print("🎮 MONOPOLY SERVER - ĐÃ SẴN SÀNG!")
        print("=" * 60)
        print(f"   🌐 TCP: {SERVER_CONFIG.tcp_host}:{SERVER_CONFIG.tcp_port}")
        print(f"   🏠 Phòng: {len(self.room_manager.rooms)}")
        clients_count = (
            len(self.tcp_handler.connected_clients)
            if hasattr(self.tcp_handler, "connected_clients")
            else 0
        )
        print(f"   👥 Client: {clients_count}")
        multicast_count = (
            len(self.multicast_manager.groups)
            if self.multicast_manager and hasattr(self.multicast_manager, "groups")
            else 0
        )
        print(f"   📡 Multicast: {multicast_count} phòng")
        print(f"   ⚡ Tick Rate: {getattr(SERVER_CONFIG, 'tick_rate', 1)}s")
        print("=" * 60)
        print("   Nhấn Ctrl+C để dừng server")
        print("=" * 60 + "\n")

    def signal_handler(self, sig, frame):
        """Xử lý signal để shutdown graceful"""
        self.logger.warning("⚠️ Nhận được signal, đang dừng server...")
        self.running[0] = False

    def _windows_signal_monitor(self):
        """Monitor Ctrl+C cho Windows (fallback)"""
        import time
        while self.running[0]:
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                self.signal_handler(None, None)
                break

    async def shutdown(self, tasks):
        """Dọn dẹp tài nguyên khi tắt server"""
        self.logger.info("🛑 Đang dừng server...")

        try:
            if hasattr(self.udp_handler, "broadcast_system_message"):
                for room_id in self.room_manager.rooms.keys():
                    try:
                        await self.udp_handler.broadcast_system_message(
                            room_id, "🔴 Máy chủ đang tắt..."
                        )
                    except Exception as e:
                        self.logger.warning(
                            f"⚠️ Không thể gửi shutdown message đến {room_id}: {e}"
                        )
        except Exception as e:
            self.logger.warning(f"⚠️ Lỗi khi gửi shutdown messages: {e}")

        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5)
                except asyncio.TimeoutError:
                    self.logger.warning(f"⚠️ Task {task.get_name()} hủy timeout")
                except asyncio.CancelledError:
                    pass

        if self.multicast_manager and hasattr(self.multicast_manager, "cleanup_all_groups"):
            try:
                self.multicast_manager.cleanup_all_groups()
                self.logger.info("✅ Đã dọn dẹp multicast groups")
            except Exception as e:
                self.logger.error(f"❌ Lỗi dọn dẹp multicast: {e}")

        await asyncio.sleep(1)
        self.logger.info("✅ Server đã dừng hoàn toàn")


async def main():
    server = MonopolyServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng server!")
    except Exception as e:
        print(f"💥 Server bị lỗi: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    print("🚀 Đang khởi động Monopoly Server...")
    print("   Đảm bảo client sử dụng cùng host và port")
    print("   Mặc định: localhost:5050")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Đã dừng server!")
    except Exception as e:
        print(f"💥 Server bị lỗi: {e}")
        import traceback
        print(traceback.format_exc())
