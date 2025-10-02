"""
UI hiển thị board và trạng thái game trong console - Phiên bản cải tiến
"""

import os
import asyncio
from typing import Dict, List, Optional
from ..shared import constants as C

class MonopolyUI:
    def __init__(self, client=None):
        self.client = client
        self.game_state = None
        self.player_name = None
        self.board_size = C.BOARD_SIZE
        self.last_messages = []
        
    def set_player_name(self, name: str):
        """Set tên player hiện tại"""
        self.player_name = name
        
    def update_game_state(self, state: dict):
        """Cập nhật trạng thái game"""
        self.game_state = state
        
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
        print("📍 Ví dụ: /join Alice")
        print()
        print("=" * 60)
        
    def display_game_state(self):
        """Hiển thị trạng thái game hiện tại"""
        if not self.game_state:
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
            turn_indicator = "👑" if current_player == self.player_name else "⏰"
            print(f"🎲 LƯỢT CHƠI: {turn_indicator} {current_player}")
        print()
        
        # Players info
        self.display_players_info()
        print()
        
        # Board visualization
        self.display_board_simple()
        print()
        
        # Current player details
        if self.player_name:
            self.display_current_player_details()
            
        print("=" * 60)
        print("💬 Tin nhắn gần đây:")
        for msg in self.last_messages[-3:]:  # Hiển thị 3 tin nhắn gần nhất
            print(f"   {msg}")
        print()
        print("📍 Gõ /help để xem hướng dẫn lệnh")
        print("=" * 60)
        
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
            is_current_player = name == self.player_name
            is_current_turn = i == self.game_state.get("current_turn", 0)
            
            player_marker = "👑" if is_current_player else "👤"
            turn_marker = " 🎲" if is_current_turn else ""
            
            print(f"{player_marker} {name}{turn_marker}")
            print(f"   💰 ${money:,} | 📍 Vị trí: {position}")
            
            if properties:
                prop_list = ", ".join(properties[:2])  # Hiển thị 2 properties đầu
                if len(properties) > 2:
                    prop_list += f" ...(+{len(properties)-2})"
                print(f"   🏠 {prop_list}")
            print()
            
    def display_board_simple(self):
        """Hiển thị board dạng đơn giản"""
        players = self.game_state.get("players", [])
        if not players:
            return
            
        print("🗺️ BẢN ĐỒ HIỆN TẠI:")
        print("-" * 50)
        
        # Tạo board trống
        board_display = ["[  ]"] * 40
        
        # Đánh dấu vị trí players
        for player in players:
            pos = player.get("position", 0)
            name_char = player["name"][0].upper() if player["name"] else "?"
            
            # Nếu có nhiều player cùng vị trí
            if board_display[pos] == "[  ]":
                board_display[pos] = f"[{name_char} ]"
            else:
                # Thêm player vào ô đã có player
                current = board_display[pos][1]  # Lấy ký tự hiện tại
                if current != " ":
                    board_display[pos] = f"[{current}{name_char}]"
        
        # Hiển thị board thành 4 hàng
        print("    " + " ".join(f"{i:2d}" for i in range(0, 10)))
        print("    " + " ".join(board_display[0:10]))
        print()
        
        print("    " + " ".join(f"{i:2d}" for i in range(10, 20)))
        print("    " + " ".join(board_display[10:20]))
        print()
        
        print("    " + " ".join(f"{i:2d}" for i in range(20, 30)))
        print("    " + " ".join(board_display[20:30]))
        print()
        
        print("    " + " ".join(f"{i:2d}" for i in range(30, 40)))
        print("    " + " ".join(board_display[30:40]))
        
    def display_current_player_details(self):
        """Hiển thị thông tin chi tiết của player hiện tại"""
        if not self.player_name or not self.game_state:
            return
            
        players = self.game_state.get("players", [])
        current_player = None
        for player in players:
            if player.get("name") == self.player_name:
                current_player = player
                break
                
        if not current_player:
            return
            
        print("👤 THÔNG TIN CỦA BẠN:")
        print("-" * 40)
        
        money = current_player.get("money", 0)
        position = current_player.get("position", 0)
        properties = current_player.get("properties", [])
        
        print(f"💰 Số dư: ${money:,}")
        print(f"📍 Vị trí hiện tại: {position}")
        print(f"🏠 Số properties: {len(properties)}")
        
        if properties:
            print(f"📋 Danh sách properties:")
            for i, prop in enumerate(properties, 1):
                print(f"   {i}. {prop}")
                
        # Hiển thị thông tin lượt chơi
        current_turn_idx = self.game_state.get("current_turn", 0)
        if current_turn_idx < len(players) and players[current_turn_idx]["name"] == self.player_name:
            print()
            print("🎲 ĐẾN LƯỢT BẠN! Gõ /roll để gieo xúc xắc")
        
    def display_message(self, message: str, msg_type: str = "info"):
        """Hiển thị message từ server"""
        # Thêm vào lịch sử tin nhắn
        if len(self.last_messages) >= 5:  # Giữ tối đa 5 tin
            self.last_messages.pop(0)
        
        if msg_type == "error":
            formatted = f"❌ {message}"
        elif msg_type == "success":
            formatted = f"✅ {message}"
        elif msg_type == "warning":
            formatted = f"⚠️ {message}"
        elif msg_type == "broadcast":
            formatted = f"📢 {message}"
        elif msg_type == "debug":
            formatted = f"🐛 {message}"
        else:  # info
            formatted = f"ℹ️ {message}"
            
        self.last_messages.append(formatted)
        
        # Cũng in ra console để hiển thị ngay lập tức
        print(formatted)
        
    def display_chat(self, sender: str, message: str):
        """Hiển thị chat message"""
        chat_msg = f"💬 {sender}: {message}"
        self.last_messages.append(chat_msg)
        print(chat_msg)
        
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
            self.display_message("✅ Đã kết nối đến server", "success")
        else:
            self.display_message("❌ Mất kết nối đến server", "error")
            
    def display_game_ended(self, winner: str = None):
        """Hiển thị khi game kết thúc"""
        print("🎉" * 20)
        print("🏁          GAME KẾT THÚC!          🏁")
        print("🎉" * 20)
        if winner:
            if winner == self.player_name:
                print(f"🎊 CHÚC MỪNG! Bạn là người thắng cuộc! 🎊")
            else:
                print(f"🎊 Người thắng: {winner}")
        print("Cảm ơn bạn đã chơi Monopoly!")
        print("🎉" * 20)