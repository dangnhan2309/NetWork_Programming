import asyncio
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_client import MonopolyGameClient

class MenuManager:
    def __init__(self, client: 'MonopolyGameClient'):
        self.client = client

    async def _join_random_room(self):
        try:
            self.client.player_name = await self._get_input("👤 Tên của bạn: ")
            self.client.player_name = self.client.player_name.strip() or f"Player{self._random_id()}"
            print("🔍 Đang tìm phòng ngẫu nhiên...")
            
            response = await self.client.tcp_client.send_command("JOIN_RANDOM", {
                "player_name": self.client.player_name
            })
            
            if response and response.get('status') == 'OK':
                data = response.get('data', {})
                await self.client.join_room_success(data)
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                print(f"❌ Không thể tham gia phòng ngẫu nhiên: {error_msg}")
                
        except Exception as e:
            print(f"❌ Lỗi khi tham gia phòng ngẫu nhiên: {e}")

    async def create_room(self):
        try:
            print("\n🏠 TẠO PHÒNG MỚI")
            print("-" * 20)
            
            if not self.client.player_name:
                self.client.player_name = await self._get_input("👤 Tên của bạn: ")
                if not self.client.player_name:
                    print("❌ Tên không được để trống")
                    return
            else:
                print(f"👤 Tên của bạn: {self.client.player_name}")
            
            room_name = await self._get_input("🏠 Tên phòng: ")
            if not room_name:
                print("❌ Tên phòng không được để trống")
                return
                
            max_players_str = await self._get_input("👥 Số lượng người chơi tối đa (mặc định 4): ")
            max_players = 4
            if max_players_str:
                try:
                    max_players = int(max_players_str)
                    if max_players < 2 or max_players > 8:
                        print("⚠️ Số người chơi phải từ 2-8, sử dụng mặc định 4")
                        max_players = 4
                except ValueError:
                    print("⚠️ Số không hợp lệ, sử dụng mặc định 4")
            
            print(f"🔍 Đang tạo phòng '{room_name}'...")
            
            response = await self.client.tcp_client.send_command("CREATE_ROOM", {
                "room_name": room_name,
                "max_players": max_players,
                "player_name": self.client.player_name
            }, timeout=15.0)
            
            if response and response.get("status") == "OK":
                print("✅ Tạo phòng thành công!")
            elif response and response.get("status") == "PENDING":
                print("🔄 Đã gửi yêu cầu tạo phòng, đang chờ phản hồi...")
            else:
                print("🔄 Đã gửi yêu cầu tạo phòng... (Response sẽ được xử lý async)")
                
        except Exception as e:
            print(f"❌ Lỗi khi tạo phòng: {e}")
            import traceback
            traceback.print_exc()

    async def _join_room(self):
        try:
            self.client.player_name = await self._get_input("👤 Tên của bạn: ")
            self.client.player_name = self.client.player_name.strip()
            if not self.client.player_name:
                print("❌ Tên không được để trống")
                return
                
            room_id = await self._get_input("🆔 Mã phòng: ")
            room_id = room_id.strip()
            
            if not room_id:
                print("❌ Vui lòng nhập mã phòng.")
                return
                
            print(f"🔍 Đang tham gia phòng '{room_id}'...")
            response = await self.client.tcp_client.send_command("JOIN_ROOM", {
                "room_id": room_id, 
                "player_name": self.client.player_name
            })
            
            if response and response.get('status') in ['OK', 'PENDING']:
                print("🔄 Đã gửi yêu cầu tham gia phòng... (Chờ phản hồi từ server)")
            else:
                print("❌ Không thể tham gia phòng.")
                    
        except Exception as e:
            print(f"❌ Lỗi tham gia phòng: {e}")

    async def _list_rooms(self):
        print("🔍 Đang lấy danh sách phòng...")
        response = await self.client.tcp_client.send_command("LIST_ROOMS")
        
        if response and response.get('status') == 'OK':
            self._display_room_list(response.get('data', {}))
        else:
            print("❌ Không nhận được danh sách phòng từ server")
        
        await self._get_input("\n👆 Nhấn Enter để tiếp tục... ")

    def _display_room_list(self, data: dict):
        print("\n📋 DANH SÁCH PHÒNG:")
        print("=" * 50)
        if not data:
            print("📭 Không có phòng nào")
            return
        for room_id, room_info in data.items():
            players = room_info.get('players', [])
            multicast_ip = room_info.get('multicast_ip', 'N/A')
            port = room_info.get('port', 'N/A')
            room_name = room_info.get('room_name', room_id)
            max_players = room_info.get('max_players', 4)
            
            print(f"🏠 {room_name} ({room_id})")
            print(f"  👥 {len(players)}/{max_players} người chơi: {', '.join(players)}")
            print(f"  🌐 {multicast_ip}:{port}")
            print("-" * 30)

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _random_id(self, min_val: int = 100, max_val: int = 999) -> int:
        import random
        return random.randint(min_val, max_val)

    async def show_main_menu(self):
        self._clear_screen()
        print("🎯 MONOPOLY MULTICAST CLIENT")
        print("=" * 40)
        print("1. 🎮 Vào phòng ngẫu nhiên (Nhanh)")
        print("2. 🏠 Tạo phòng mới")
        print("3. 🚪 Tham gia phòng có sẵn") 
        print("4. 📋 Danh sách phòng")
        print("5. ❌ Thoát")
        print("=" * 40)
        
        try:
            choice = await self._get_input("👉 Chọn [1-5]: ")
            choice = choice.strip()
            
            if choice == "1":
                await self._join_random_room()
            elif choice == "2":
                await self.create_room()
            elif choice == "3":
                await self._join_room()
            elif choice == "4":
                await self._list_rooms()
            elif choice == "5":
                self.client.running = False
            else:
                print("❌ Lựa chọn không hợp lệ.")
                await asyncio.sleep(2)
                
        except (KeyboardInterrupt, EOFError):
            self.client.running = False

    async def _get_input(self, prompt: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)

    def _show_help(self):
        print("""
📘 LỆNH TRONG PHÒNG:
/status            → Xem trạng thái game
/chat <nội dung>   → Gửi tin nhắn
/roll              → Tung xúc xắc
/buy               → Mua tài sản
/end               → Kết thúc lượt
/state             → Trạng thái game
/players           → Xem người chơi
/start             → Bắt đầu game (chủ phòng)
/board             → Xem bàn cờ
/test              → Test kết nối
/help              → Trợ giúp
/exit              → Rời phòng

🎯 TỰ ĐỘNG:
• Game sẽ tự động bắt đầu khi đủ số người chơi
• Bàn cờ sẽ tự động hiển thị khi game bắt đầu
• Dùng /status để kiểm tra trạng thái hiện tại
""")
