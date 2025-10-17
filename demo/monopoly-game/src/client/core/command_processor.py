# src/client/core/command_processor.py
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_client import MonopolyGameClient

class CommandProcessor:
    def __init__(self, client: 'MonopolyGameClient'):
        self.client = client

    async def process_command(self, command: str):
        """Xử lý command từ người dùng - ĐÃ SỬA SYNTAX"""
        try:
            parts = command.strip().split()
            if not parts:
                return

            cmd = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd == "/state":
                await self._handle_state_command()
            elif cmd == "/board":
                await self._handle_board_command()
            elif cmd == "/roll":
                await self._handle_roll_command()
            elif cmd == "/start":
                await self._handle_start_command()
            elif cmd == "/chat" and args:
                await self._handle_chat_command(" ".join(args))
            elif cmd == "/players":
                await self._handle_players_command()
            elif cmd == "/test":
                await self._handle_test_command()
            elif cmd == "/help":
                await self._handle_help_command()
            elif cmd == "/exit":
                await self._handle_exit_command()
            else:
                print("❌ Lựa chọn không hợp lệ.")
                print("💡 Sử dụng /help để xem các lệnh có sẵn")
                
        except Exception as e:
            print(f"❌ Lỗi xử lý command: {e}")

    async def _handle_state_command(self):
        """Xử lý lệnh /state - request state từ server"""
        if not self.client.in_room:
            print("❌ Bạn chưa trong phòng nào")
            return
            
        print("🔄 Đang yêu cầu trạng thái game từ server...")
        response = await self.client.send_game_command("GET_GAME_STATE")
        
        if response and response.get("status") == "OK":
            print("✅ Đã cập nhật trạng thái game")
        else:
            print("❌ Không thể lấy trạng thái game")

    async def _handle_board_command(self):
        """Xử lý lệnh /board - hiển thị bàn cờ"""
        await self.client.game_ui.show_board()

    async def _handle_roll_command(self):
        """Xử lý lệnh /roll - tung xúc xắc"""
        if not self.client.in_room:
            print("❌ Bạn chưa trong phòng nào")
            return
            
        if not self.client._game_started:
            print("❌ Game chưa bắt đầu")
            return
            
        print("🎲 Đang tung xúc xắc...")
        response = await self.client.send_game_command("ROLL_DICE")
        
        if response and response.get("status") == "OK":
            print("✅ Đã tung xúc xắc")
        else:
            print("❌ Không thể tung xúc xắc")

    async def _handle_start_command(self):
        """Xử lý lệnh /start - bắt đầu game"""
        if not self.client.in_room:
            print("❌ Bạn chưa trong phòng nào")
            return
            
        if not self.client.is_host:
            print("❌ Chỉ chủ phòng mới có thể bắt đầu game")
            return
            
        print("🚀 Đang bắt đầu game...")
        response = await self.client.send_game_command("START_GAME")
        
        if response and response.get("status") == "OK":
            print("✅ Đã bắt đầu game")
        else:
            print("❌ Không thể bắt đầu game")

    async def _handle_chat_command(self, message: str):
        """Xử lý lệnh /chat - gửi tin nhắn"""
        if not self.client.in_room:
            print("❌ Bạn chưa trong phòng nào")
            return
            
        await self.client.send_chat_message(message)

    async def _handle_players_command(self):
        """Xử lý lệnh /players - xem người chơi"""
        if not self.client.in_room:
            print("❌ Bạn chưa trong phòng nào")
            return
            
        print(f"👥 Số người trong phòng: {self.client._last_player_count}/{self.client._max_players}")

    async def _handle_test_command(self):
        """Xử lý lệnh /test - test kết nối"""
        if not self.client.in_room:
            print("❌ Bạn chưa trong phòng nào")
            return
            
        print("🛠️ Đang test kết nối multicast...")
        await self.client._test_multicast_connection()

    async def _handle_help_command(self):
        """Xử lý lệnh /help - hiển thị trợ giúp"""
        self.client.show_room_help()

    async def _handle_exit_command(self):
        """Xử lý lệnh /exit - rời phòng"""
        await self.client.leave_room()

    async def handle_game_event(self, action: str, payload: dict, sender: str):
        """Xử lý sự kiện game từ multicast"""
        try:
            if action == "CHAT":
                message = payload.get("message", "")
                player = payload.get("player", "Unknown")
                print(f"💬 {player}: {message}")
            elif action == "GAME_STARTED":
                print("🚀 Game đã bắt đầu!")
            elif action == "PLAYER_JOINED":
                player_name = payload.get("player_name", "")
                print(f"🎊 {player_name} đã tham gia phòng!")
            elif action == "PLAYER_LEFT":
                player_name = payload.get("player_name", "")
                print(f"👋 {player_name} đã rời phòng!")
                
        except Exception as e:
            print(f"❌ Lỗi xử lý game event: {e}")