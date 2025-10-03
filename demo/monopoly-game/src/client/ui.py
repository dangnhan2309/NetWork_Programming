
"""
UI hiển thị board và trạng thái game trong console - Phiên bản cải tiến
"""

import os
import asyncio
from typing import Dict, List, Optional
from src.shared import constants as C
from src.server.board import Board

class MonopolyUI:
    def __init__(self, client=None):
        self.client = client
        self.game_state = None
        self.player_name = None
        self.board_size = C.BOARD_SIZE
        self.last_messages = []
        self.board = Board()
        self.has_rolled_this_turn = False
        
    def set_player_name(self, name: str):
        """Set tên player hiện tại"""
        self.player_name = name
        
    def update_game_state(self, state: dict):
        """Cập nhật trạng thái game"""
        self.game_state = state
        
        # DEBUG: Hiển thị thông tin state
        if state:
            print(f"🔧 DEBUG UI: Received game state - players: {[p.get('name', '?') for p in state.get('players', [])]}")
            print(f"🔧 DEBUG UI: Current turn: {state.get('current_turn', '?')}")
            print(f"🔧 DEBUG UI: My name: {self.player_name}")
            
            current_turn_idx = state.get("current_turn", 0)
            players = state.get("players", [])
            if players and current_turn_idx < len(players):
                current_player = players[current_turn_idx].get("name", "")
                print(f"🔧 DEBUG UI: Current player should be: {current_player}")
                print(f"🔧 DEBUG UI: Is it my turn? {current_player.lower() == self.player_name.lower() if self.player_name else False}")
        
        # Reset trạng thái roll khi có lượt mới
        if state and state.get("current_turn") is not None:
            current_turn_idx = state.get("current_turn", 0)
            players = state.get("players", [])
            if players and current_turn_idx < len(players):
                current_player = players[current_turn_idx].get("name", "")
                # So sánh không phân biệt hoa thường
                if self.player_name and current_player.lower() == self.player_name.lower():
                    self.has_rolled_this_turn = False
                    print(f"🔧 DEBUG UI: Reset roll state for new turn")
        
    def clear_screen(self):
        """Xóa màn hình console"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def display_welcome(self):
        """Hiển thị màn hình chào mừng"""
        self.clear_screen()
        print("🎲" * 30)
        print("🎯      MONOPOLY MULTIPLAYER GAME      🎯")
        print("🎲" * 30)
        print()
        print("Chào mừng bạn đến với game Monopoly!")
        print("📍 Gõ /join <tên> để tham gia game")
        print("📍 Gõ /help để xem danh sách lệnh")
        print("📍 Ví dụ: /join Thuy")
        print()
        print("=" * 60)
        
    def display_game_state(self):
        """Hiển thị trạng thái game hiện tại"""
        if not self.game_state:
            self.display_welcome()
            return
            
        self.clear_screen()
        
        # Header
        print("🎲" * 35)
        print("🎯          MONOPOLY GAME STATE          🎯")
        print("🎲" * 35)
        print()
        
        # Game status
        game_status = self.game_state.get("state", "unknown").upper()
        current_turn_idx = self.game_state.get("current_turn", 0)
        players = self.game_state.get("players", [])
        
        status_emoji = {
            "WAITING": "⏳",
            "PLAYING": "🎮", 
            "ENDED": "🏁"
        }
        
        print(f"📊 TRẠNG THÁI: {status_emoji.get(game_status, '❓')} {game_status}")
        
        # Current turn
        if players and current_turn_idx < len(players):
            current_player = players[current_turn_idx]["name"]
            is_my_turn = current_player.lower() == self.player_name.lower() if self.player_name else False
            turn_indicator = "👑 BẠN" if is_my_turn else "⏰"
            
            if is_my_turn:
                print(f"🎲 LƯỢT CHƠI HIỆN TẠI: {turn_indicator}")
                if not self.has_rolled_this_turn:
                    print("💡 Bạn có thể: /roll - gieo xúc xắc")
                else:
                    print("💡 Bạn có thể: /buy - mua nhà, /end - kết thúc lượt")
            else:
                print(f"🎲 LƯỢT CHƠI HIỆN TẠI: {turn_indicator} {current_player}")
        print()
        
        # Hiển thị board đẹp từ server
        self.display_board_server_style()
        print()
        
        # Players info
        self.display_players_info()
        print()
        
        # Current player details
        if self.player_name:
            self.display_current_player_details()
            
        # Recent messages
        if self.last_messages:
            print("=" * 60)
            print("💬 TIN NHẮN GẦN ĐÂY:")
            for msg in self.last_messages[-3:]:
                print(f"   {msg}")
        
        print("=" * 60)
        print("📍 Gõ /help để xem hướng dẫn lệnh")
        print("=" * 60)
        
    def display_board_server_style(self):
        """Hiển thị board giống như server"""
        players = self.game_state.get("players", [])
        if not players:
            return
            
        # Tạo dictionary player positions từ game state
        player_positions = {}
        for player in players:
            name = player.get("name", "Unknown")
            position = player.get("position", 0)
            player_positions[name] = position
            
        print("🗺️ BẢN ĐỒ TRÒ CHƠI:")
        print("-" * 50)
        
        # Render board với player positions
        self.board.render_board(player_positions)
        
    def display_players_info(self):
        """Hiển thị thông tin tất cả players"""
        players = self.game_state.get("players", [])
        if not players:
            print("👥 CHƯA CÓ NGƯỜI CHƠI...")
            return
            
        print("👥 DANH SÁCH NGƯỜI CHƠI:")
        print("-" * 50)
        
        for i, player in enumerate(players):
            name = player.get("name", "Unknown")
            money = player.get("money", 0)
            position = player.get("position", 0)
            properties = player.get("properties", [])
            
            # Highlight current player và current turn
            is_current_player = name.lower() == self.player_name.lower() if self.player_name else False
            is_current_turn = i == self.game_state.get("current_turn", 0)
            
            player_marker = "👑 BẠN" if is_current_player else "👤"
            turn_marker = " 🎲 (ĐANG CHƠI)" if is_current_turn else ""
            
            print(f"{player_marker} {name}{turn_marker}")
            print(f"   💰 ${money:,} | 📍 Vị trí: {position}")
            
            if properties:
                print(f"   🏠 Sở hữu: {len(properties)} property(s)")
                if len(properties) <= 3:
                    prop_list = ", ".join(properties)
                    print(f"      {prop_list}")
                else:
                    prop_list = ", ".join(properties[:3])
                    print(f"      {prop_list} ...(+{len(properties)-3})")
            else:
                print(f"   🏠 Chưa có property nào")
            print()
            
    def display_current_player_details(self):
        """Hiển thị thông tin chi tiết của player hiện tại"""
        if not self.player_name or not self.game_state:
            return
            
        players = self.game_state.get("players", [])
        current_player = None
        for player in players:
            if player.get("name", "").lower() == self.player_name.lower():
                current_player = player
                break
                
        if not current_player:
            return
            
        print("👤 THÔNG TIN CHI TIẾT CỦA BẠN:")
        print("-" * 40)
        
        money = current_player.get("money", 0)
        position = current_player.get("position", 0)
        properties = current_player.get("properties", [])
        
        print(f"💰 Số dư: ${money:,}")
        print(f"📍 Vị trí hiện tại: {position}")
        
        # Hiển thị thông tin ô hiện tại
        tile = self.board.get_tile(position)
        print(f"🏠 Ô hiện tại: {tile['name']} ({tile['type']})")
        if tile.get('price', 0) > 0:
            print(f"💵 Giá: ${tile['price']}")
        if tile.get('rent', 0) > 0:
            print(f"📈 Tiền thuê: ${tile['rent']}")
            
        print(f"📋 Tổng số properties: {len(properties)}")
        
        if properties:
            print(f"🏘️ Danh sách properties của bạn:")
            for i, prop in enumerate(properties, 1):
                print(f"   {i}. {prop}")
        
        # Kiểm tra xem có phải lượt của mình không
        current_turn_idx = self.game_state.get("current_turn", 0)
        if current_turn_idx < len(players) and players[current_turn_idx]["name"].lower() == self.player_name.lower():
            print()
            print("🎲 🎲 🎲 ĐẾN LƯỢT BẠN! 🎲 🎲 🎲")
            if not self.has_rolled_this_turn:
                print("💡 Gõ /roll để gieo xúc xắc")
            else:
                print("💡 Các lệnh có thể dùng:")
                print("   /buy  - Mua property hiện tại (nếu có thể)")
                print("   /end  - Kết thúc lượt")
                print("   /chat <tin nhắn> - Gửi tin nhắn")
                
    def display_message(self, message: str, msg_type: str = "info"):
        """Hiển thị message từ server"""
        # Thêm vào lịch sử tin nhắn
        if len(self.last_messages) >= 5:
            self.last_messages.pop(0)
        
        if msg_type == "error":
            formatted = f"❌ LỖI: {message}"
        elif msg_type == "success":
            formatted = f"✅ THÀNH CÔNG: {message}"
        elif msg_type == "warning":
            formatted = f"⚠️ CẢNH BÁO: {message}"
        elif msg_type == "broadcast":
            formatted = f"📢 THÔNG BÁO: {message}"
        elif msg_type == "debug":
            formatted = f"🐛 DEBUG: {message}"
        else:
            formatted = f"ℹ️ THÔNG TIN: {message}"
            
        self.last_messages.append(formatted)
        
        # Hiển thị ngay lập tức
        print(f"\n{formatted}\n")
        
    def display_chat(self, sender: str, message: str):
        """Hiển thị chat message"""
        chat_msg = f"💬 {sender}: {message}"
        self.last_messages.append(chat_msg)
        print(f"\n{chat_msg}\n")
        
    def mark_rolled(self):
        """Đánh dấu đã roll trong lượt này"""
        self.has_rolled_this_turn = True
        
    def reset_turn_state(self):
        """Reset trạng thái lượt chơi"""
        self.has_rolled_this_turn = False
        
    async def get_input_async(self):
        """Lấy input từ người dùng (async)"""
        loop = asyncio.get_event_loop()
        prompt = f"[{self.player_name}] > " if self.player_name else "> "
        try:
            user_input = await loop.run_in_executor(None, input, prompt)
            return user_input.strip()
        except (EOFError, KeyboardInterrupt):
            return "/exit"
            
    def get_input_prompt(self) -> str:
        """Lấy prompt cho input (sync)"""
        return f"[{self.player_name}] > " if self.player_name else "> "
        
    def display_connection_status(self, connected: bool):
        """Hiển thị trạng thái kết nối"""
        if connected:
            self.display_message("Đã kết nối đến server thành công", "success")
        else:
            self.display_message("Mất kết nối đến server", "error")
            
    def display_game_ended(self, winner: str = None):
        """Hiển thị khi game kết thúc"""
        print("\n" + "🎉" * 20)
        print("🏁          GAME KẾT THÚC!          🏁")
        print("🎉" * 20)
        if winner:
            if winner.lower() == self.player_name.lower() if self.player_name else False:
                print(f"🎊 CHÚC MỪNG! Bạn là người thắng cuộc! 🎊")
            else:
                print(f"🎊 Người thắng: {winner}")
        print("Cảm ơn bạn đã chơi Monopoly!")
        print("🎉" * 20)
        
    def display_help(self):
        """Hiển thị hướng dẫn lệnh"""
        print("\n📚 DANH SÁCH LỆNH:")
        print("-" * 40)
        print("/join <tên>    - Tham gia game")
        print("/roll         - Gieo xúc xắc (chỉ trong lượt của bạn)")
        print("/buy          - Mua property hiện tại")
        print("/end          - Kết thúc lượt")
        print("/chat <msg>   - Gửi tin nhắn chat")
        print("/state        - Làm mới trạng thái game")
        print("/help         - Hiển thị trợ giúp")
        print("/exit         - Thoát game")
        print("-" * 40)
        print("💡 Lưu ý: Bạn chỉ có thể /roll một lần mỗi lượt")

