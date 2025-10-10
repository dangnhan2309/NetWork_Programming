import asyncio
import socket
import struct
import json
import os
import random
import uuid
import datetime
import traceback
from typing import Dict, Optional

class MonopolyMulticastClient:
    def __init__(self, server_host='localhost', server_port=5050):
        self.server_host = server_host
        self.server_port = server_port
        self.player_name: Optional[str] = None
        self.room_id: Optional[str] = None
        self.group_ip: Optional[str] = None
        self.port: Optional[int] = None
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.udp_socket: Optional[socket.socket] = None
        self.running = True
        self.is_host = False
        self.connected = False
        self.in_room = False
        self._response_event = asyncio.Event()
        self._last_response = None
        self._tcp_task = None
        self._pending_commands = {}  # Track pending commands

    async def connect_tcp(self):
        """Kết nối TCP đến server"""
        print(f"🔍 Đang kết nối đến {self.server_host}:{self.server_port}")
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.server_host, self.server_port
            )
            self.connected = True
            print(f"✅ Kết nối TCP thành công")
            
            # Bắt đầu task nhận tin nhắn
            self._tcp_task = asyncio.create_task(self.receive_tcp_messages())
            return True
        except Exception as e:
            print(f"❌ Lỗi kết nối TCP: {e}")
            return False

    async def send_tcp_command(self, command, data=None):
        """Gửi lệnh TCP đến server và chờ response - ĐÃ SỬA TIMEOUT"""
        if not self.connected or not self.writer:
            print("❌ Không thể gửi - không kết nối đến server")
            return None
            
        try:
            packet = {
                "cmd": command,
                "data": data or {}
            }
            message = json.dumps(packet) + "\n"
            encoded_message = message.encode('utf-8')
            
            print(f"📤 Đang gửi lệnh: {command}")
            
            # Reset event và response
            self._response_event.clear()
            self._last_response = None
            
            # Gửi lệnh
            self.writer.write(encoded_message)
            await self.writer.drain()
            print(f"✅ Đã gửi lệnh {command}")
            
            # Chờ response với timeout - TĂNG THỜI GIAN CHỜ
            try:
                await asyncio.wait_for(self._response_event.wait(), timeout=15.0)  # Tăng từ 10 lên 15 giây
                response = self._last_response
                if response:
                    print(f"📥 Nhận response: {response.get('cmd')} - {response.get('status')}")
                return response
            except asyncio.TimeoutError:
                print(f"⏰ TIMEOUT: Không nhận được response sau 15 giây")
                return None
                
        except Exception as e:
            print(f"❌ Lỗi gửi lệnh {command}: {e}")
            self.connected = False
            return None

    async def receive_tcp_messages(self):
        """Nhận message từ TCP server"""
        print(f"🔍 Bắt đầu nhận TCP messages...")
        buffer = ""
        
        while self.connected and self.reader and self.running:
            try:
                # Đọc dữ liệu với timeout
                data = await asyncio.wait_for(self.reader.read(4096), timeout=1.0)
                
                if not data:
                    print("🔌 Server đã ngắt kết nối")
                    self.connected = False
                    break

                chunk = data.decode('utf-8')
                buffer += chunk
                print(f"📨 Nhận {len(data)} bytes, buffer: {len(buffer)} chars")
                
                # Xử lý tất cả message hoàn chỉnh trong buffer
                while '\n' in buffer:
                    line_end = buffer.find('\n')
                    message_str = buffer[:line_end].strip()
                    buffer = buffer[line_end + 1:]
                    
                    if message_str:
                        print(f"🔍 Xử lý message: {message_str[:100]}...")
                        await self.process_tcp_message(message_str)
                        
            except asyncio.TimeoutError:
                # Timeout là bình thường, tiếp tục vòng lặp
                continue
            except asyncio.CancelledError:
                print("🔍 TCP receiver bị cancelled")
                break
            except Exception as e:
                print(f"❌ Lỗi nhận TCP: {e}")
                if self.connected:
                    await asyncio.sleep(0.5)
                else:
                    break

    async def process_tcp_message(self, message_str: str):
        """Xử lý một message TCP hoàn chỉnh - ĐÃ SỬA XỬ LÝ RESPONSE"""
        try:
            response = json.loads(message_str)
            cmd = response.get("cmd")
            status = response.get("status", "UNKNOWN")
            data = response.get("data", {})
            message = response.get("message", "")
            
            print(f"📥 Nhận response: {cmd} - {status}")
            
            if status == "ERROR":
                print(f"❌ Lỗi từ server: {message}")
            else:
                if cmd == "ROOM_LIST":
                    self.display_room_list(data)
                elif cmd == "ROOM_CREATED":
                    await self.handle_room_created(data)
                elif cmd == "JOIN_SUCCESS":
                    await self.handle_join_success(data)
                elif cmd == "LEAVE_RESULT":
                    print("✅ Đã rời phòng")
                    await self.leave_room()

            # QUAN TRỌNG: Set response ngay cả khi đã timeout
            self._last_response = response
            self._response_event.set()
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"🔍 Message: {message_str}")

    def display_room_list(self, data):
        """Hiển thị danh sách phòng"""
        print("\n📋 DANH SÁCH PHÒNG:")
        print("=" * 50)
        
        if not data:
            print("📭 Không có phòng nào")
            return
            
        for room_id, room_info in data.items():
            players = room_info.get('players', [])
            multicast_ip = room_info.get('multicast_ip', 'N/A')
            port = room_info.get('port', 'N/A')
            
            print(f"🏠 {room_id}")
            print(f"  👥 {len(players)} người chơi: {', '.join(players)}")
            print(f"  🌐 {multicast_ip}:{port}")
            print("-" * 30)

    async def handle_room_created(self, data):
        """Xử lý tạo phòng thành công"""
        print(f"✅ Đã tạo phòng: {data.get('room_id')}")
        self.room_id = data.get('room_id')
        self.is_host = True
        
        # Tự động join phòng vừa tạo
        print(f"🔍 Tự động join phòng {self.room_id}")
        response = await self.send_tcp_command("JOIN_ROOM", {
            "room_id": self.room_id, 
            "player_name": self.player_name
        })
        
        if response and response.get('status') == 'OK':
            print("✅ Đã vào phòng thành công!")
        else:
            print("❌ Không thể vào phòng")

    async def handle_join_success(self, data):
        """Xử lý join phòng thành công"""
        print(f"🎮 Đã tham gia phòng {data.get('room_id')}")
        print(f"🌐 Multicast: {data.get('multicast_ip')}:{data.get('port')}")
        print(f"👥 Người chơi: {data.get('players', [])}")
        
        self.room_id = data.get('room_id')
        multicast_ip = data.get('multicast_ip')
        multicast_port = data.get('port')
        
        if await self.setup_multicast(multicast_ip, multicast_port):
            self.in_room = True
            asyncio.create_task(self.receive_multicast_messages())
            print("🔍 Đang lắng nghe multicast...")
            
            # Hiển thị menu trong phòng
            print("\n🎮 BẠN ĐÃ VÀO PHÒNG!")
            print("💬 Gõ /help để xem các lệnh")
        else:
            print("❌ Không thể thiết lập multicast")

    async def setup_multicast(self, multicast_ip, multicast_port):
        """Thiết lập UDP Multicast - ĐÃ SỬA LỖI CHÍNH TẢ"""
        try:
            self.group_ip = multicast_ip
            self.port = multicast_port
            
            # SỬA LỖI: IPPROTO_UDP thay vì IPPROTO_UUD
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the multicast port
            self.udp_socket.bind(('', multicast_port))
            
            # Join multicast group
            mreq = struct.pack("=4sl", socket.inet_aton(multicast_ip), socket.INADDR_ANY)
            self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            self.udp_socket.setblocking(False)
            
            print(f"✅ Đã tham gia multicast group {multicast_ip}:{multicast_port}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi thiết lập multicast: {e}")
            traceback.print_exc()  # In chi tiết lỗi
            return False
    async def run(self):
        """Chạy client chính"""
        print("🎮 MONOPOLY MULTICAST CLIENT")
        print("=============================")

        # Kết nối TCP đến server
        if not await self.connect_tcp():
            print("❌ Không thể kết nối đến server.")
            print("   Hãy chắc chắn server đang chạy: python server_fixed.py")
            return

        try:
            while self.running:
                if not self.in_room:
                    await self.main_menu()
                else:
                    await self.game_loop()
                    
        except KeyboardInterrupt:
            print("\n👋 Thoát client...")
        except Exception as e:
            print(f"❌ Lỗi không mong muốn: {e}")
            traceback.print_exc()
            
    async def main_menu(self):
        """Hiển thị menu chính"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("🎯 MONOPOLY MULTICAST CLIENT")
        print("=" * 40)
        print("1. 🏠 Tạo phòng mới")
        print("2. 🚪 Tham gia phòng có sẵn") 
        print("3. 📋 Danh sách phòng")
        print("4. ❌ Thoát")
        print("=" * 40)
        
        try:
            # Dùng asyncio để xử lý input không blocking
            choice = await asyncio.get_event_loop().run_in_executor(
                None, input, "👉 Chọn [1-4]: "
            )
            choice = choice.strip()
            
            if choice == "1":
                await self.create_room()
            elif choice == "2":
                await self.join_room()
            elif choice == "3":
                await self.list_rooms()
            elif choice == "4":
                self.running = False
            else:
                print("❌ Lựa chọn không hợp lệ.")
                await asyncio.sleep(2)
                
        except (KeyboardInterrupt, EOFError):
            self.running = False
        except Exception as e:
            print(f"❌ Lỗi trong menu: {e}")

    async def create_room(self):
        """Tạo phòng mới"""
        try:
            self.player_name = await asyncio.get_event_loop().run_in_executor(
                None, input, "👤 Tên của bạn: "
            )
            self.player_name = self.player_name.strip() or f"Player{random.randint(100,999)}"
            
            room_name = await asyncio.get_event_loop().run_in_executor(
                None, input, "🏠 Tên phòng: "
            )
            room_name = room_name.strip() or f"Room-{random.randint(1000,9999)}"
            
            print(f"🔍 Đang tạo phòng '{room_name}'...")
            response = await self.send_tcp_command("CREATE_ROOM", {"room_id": room_name})
            
            if response:
                if response.get('status') == 'OK':
                    print(f"✅ Tạo phòng thành công!")
                else:
                    print(f"❌ Tạo phòng thất bại: {response.get('message')}")
            else:
                print("❌ Không nhận được response từ server")
                
        except (KeyboardInterrupt, EOFError):
            self.running = False
        except Exception as e:
            print(f"❌ Lỗi tạo phòng: {e}")

    async def join_room(self):
        """Tham gia phòng có sẵn"""
        try:
            self.player_name = await asyncio.get_event_loop().run_in_executor(
                None, input, "👤 Tên của bạn: "
            )
            self.player_name = self.player_name.strip() or f"Player{random.randint(100,999)}"
            
            room_id = await asyncio.get_event_loop().run_in_executor(
                None, input, "🆔 Mã phòng: "
            )
            room_id = room_id.strip()
            
            if not room_id:
                print("❌ Vui lòng nhập mã phòng.")
                await asyncio.sleep(2)
                return
                
            print(f"🔍 Đang tham gia phòng '{room_id}'...")
            response = await self.send_tcp_command("JOIN_ROOM", {
                "room_id": room_id, 
                "player_name": self.player_name
            })
            
            if response:
                if response.get('status') == 'OK':
                    print(f"✅ Tham gia phòng thành công!")
                else:
                    print(f"❌ Tham gia phòng thất bại: {response.get('message')}")
            else:
                print("❌ Không nhận được response từ server")
                
        except (KeyboardInterrupt, EOFError):
            self.running = False
        except Exception as e:
            print(f"❌ Lỗi tham gia phòng: {e}")

    async def list_rooms(self):
        """Xem danh sách phòng"""
        print("🔍 Đang lấy danh sách phòng...")
        response = await self.send_tcp_command("LIST_ROOMS")
        
        if not response:
            print("❌ Không nhận được danh sách phòng từ server")
        
        # Chờ người dùng nhấn Enter
        await asyncio.get_event_loop().run_in_executor(
            None, input, "\n👆 Nhấn Enter để tiếp tục... "
        )

    async def game_loop(self):
        """Vòng lặp game khi đã trong phòng"""
        while self.in_room and self.connected and self.running:
            try:
                print(f"\n🎮 PHÒNG: {self.room_id}")
                print("💬 Gõ /help để xem lệnh, /exit để rời phòng")
                
                cmd = await asyncio.get_event_loop().run_in_executor(
                    None, input, "🎮 Lệnh: "
                )
                cmd = cmd.strip()
                
                if not cmd:
                    continue

                await self.process_command(cmd)

            except (KeyboardInterrupt, EOFError):
                await self.leave_current_room()
                break
            except Exception as e:
                print(f"❌ Lỗi: {e}")

    async def process_command(self, cmd: str):
        """Xử lý lệnh từ người dùng"""
        cmd_lower = cmd.lower()
        
        if cmd_lower == "/exit":
            await self.leave_current_room()
        elif cmd_lower == "/help":
            self.show_help()
        elif cmd_lower == "/roll":
            await self.send_game_command("ROLL")
        elif cmd_lower == "/state":
            await self.send_game_command("STATE_REQUEST")
        elif cmd_lower.startswith("/chat "):
            message = cmd[6:].strip()
            await self.send_chat_message(message)
        elif cmd_lower == "/players":
            await self.send_game_command("GET_PLAYERS")
        elif cmd_lower == "/start":
            await self.send_game_command("START_GAME")
        elif cmd_lower == "/test":
            await self.test_connection()
        else:
            print("❌ Lệnh không hợp lệ. /help để xem lệnh.")

    async def send_game_command(self, action: str, args: dict = None):
        """Gửi lệnh game đến server"""
        if not self.in_room:
            print("❌ Không trong phòng nào.")
            return
            
        packet = self.make_packet(action, args or {}, "SERVER", "COMMAND")
        if await self.send_udp_packet(packet):
            print(f"✅ Đã gửi lệnh {action}")

    async def send_chat_message(self, message: str):
        """Gửi tin nhắn chat"""
        packet = self.make_packet("CHAT", {"message": message}, "ALL", "EVENT")
        if await self.send_udp_packet(packet):
            print(f"💬 Đã gửi tin nhắn: {message}")

    async def send_udp_packet(self, packet: Dict):
        """Gửi packet UDP multicast"""
        if not self.udp_socket or not self.group_ip or not self.port:
            print("❌ Chưa kết nối multicast")
            return False
            
        try:
            loop = asyncio.get_event_loop()
            data = json.dumps(packet).encode('utf-8')
            await loop.sock_sendto(self.udp_socket, data, (self.group_ip, self.port))
            return True
        except Exception as e:
            print(f"❌ Lỗi gửi UDP: {e}")
            return False

    async def receive_multicast_messages(self):
        """Nhận message từ multicast group"""
        loop = asyncio.get_event_loop()
        while self.in_room and self.udp_socket and self.running:
            try:
                data, addr = await loop.sock_recvfrom(self.udp_socket, 4096)
                packet = json.loads(data.decode('utf-8'))
                await self.handle_multicast_packet(packet, addr)
                
            except BlockingIOError:
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.in_room:
                    await asyncio.sleep(0.1)

    async def handle_multicast_packet(self, packet: Dict, addr):
        """Xử lý packet từ multicast"""
        try:
            header = packet.get("header", {})
            if header:
                room = header.get("room_id")
                if room != self.room_id:
                    return
                    
                sender = header.get("sender")
                packet_type = header.get("type")
                action = packet.get("command", {}).get("action")
                payload = packet.get("payload", {})
                
                print(f"📨 [Multicast] {sender}: {action}")
                
                if packet_type == "STATE":
                    if action == "HEARTBEAT":
                        players = payload.get('players', [])
                        if players:
                            print(f"💓 Có {len(players)} người trong phòng: {', '.join(players)}")
                elif packet_type == "EVENT":
                    self.handle_game_event(action, payload)
                    
        except Exception as e:
            print(f"❌ Lỗi xử lý packet: {e}")

    def handle_game_event(self, action: str, payload: Dict):
        """Xử lý sự kiện game"""
        if action == "PLAYER_JOINED":
            player = payload.get("player")
            print(f"🎉 {player} đã tham gia phòng!")
        elif action == "PLAYER_LEFT":
            player = payload.get("player")
            print(f"👋 {player} đã rời phòng")
        elif action == "GAME_STARTING":
            print("🚀 Trò chơi sắp bắt đầu...")
        elif action == "CHAT":
            player = payload.get("player")
            message = payload.get("message")
            print(f"💬 {player}: {message}")

    def make_packet(self, action: str, data: dict = None, target: str = "ALL", ptype: str = "COMMAND"):
        """Tạo packet"""
        return {
            "header": {
                "packet_id": str(uuid.uuid4()),
                "room_id": self.room_id,
                "sender": self.player_name,
                "target": target,
                "type": ptype,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "version": "1.0"
            },
            "command": {
                "action": action,
                "args": data or {}
            },
            "payload": data or {}
        }

    async def test_connection(self):
        """Test kết nối"""
        print("🔍 Kiểm tra kết nối:")
        print(f"   Phòng: {self.room_id}")
        print(f"   Multicast: {self.group_ip}:{self.port}")
        print(f"   Kết nối TCP: {'✅' if self.connected else '❌'}")
        print(f"   Trong phòng: {'✅' if self.in_room else '❌'}")

    async def leave_current_room(self):
        """Rời phòng hiện tại"""
        if not self.in_room:
            return
            
        print("🔍 Đang rời phòng...")
        response = await self.send_tcp_command("LEAVE_ROOM", {
            "room_id": self.room_id, 
            "player_name": self.player_name
        })
        
        if response and response.get('status') == 'OK':
            await self.leave_room()
        else:
            print("❌ Lỗi khi rời phòng")
            await self.leave_room()

    async def leave_room(self):
        """Rời phòng (cleanup)"""
        self.in_room = False
        
        if self.udp_socket:
            try:
                if self.group_ip:
                    mreq = struct.pack("4sl", socket.inet_aton(self.group_ip), socket.INADDR_ANY)
                    self.udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
                self.udp_socket.close()
            except:
                pass
            self.udp_socket = None
        
        self.room_id = None
        self.group_ip = None
        self.port = None
        self.is_host = False
        print("🚪 Đã rời phòng")

    def show_help(self):
        """Hiển thị danh sách lệnh"""
        print("""
📘 LỆNH TRONG PHÒNG:
 /chat <nội dung>   → Gửi tin nhắn
 /roll              → Tung xúc xắc  
 /state             → Trạng thái game
 /players           → Xem người chơi
 /start             → Bắt đầu game (chủ phòng)
 /test              → Test kết nối
 /help              → Trợ giúp
 /exit              → Rời phòng
        """)

    async def cleanup(self):
        """Dọn dẹp tài nguyên"""
        print("🔍 Đang dọn dẹp...")
        self.running = False
        self.connected = False
        self.in_room = False
        
        # Hủy task TCP
        if self._tcp_task and not self._tcp_task.done():
            self._tcp_task.cancel()
            try:
                await self._tcp_task
            except asyncio.CancelledError:
                pass
        
        # Đóng writer
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
        
        # Đóng UDP socket
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except:
                pass
        print("✅ Dọn dẹp hoàn tất")

# Phần chạy trực tiếp
async def main():
    """Main function"""
    print("🎮 MONOPOLY MULTICAST CLIENT")
    print("=============================")
    
    client = MonopolyMulticastClient()
    await client.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")