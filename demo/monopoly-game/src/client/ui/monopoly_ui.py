"""
MonopolyUI - Giao diện console cho client Monopoly (UDP Multicast)
Tác giả: Jessticall x GPT-5

💡 Cách dùng:
-------------
from .ui import MonopolyUI

if __name__ == "__main__":
    ui = MonopolyUI()
    ui.set_player_name("Tester")

    # Giả lập trạng thái game để test
    fake_state = {
        "roomState": "playing",
        "currentTurn": "p2",
        "players": [
            {"id": "p1", "name": "Alice", "money": 1200, "position": 10},
            {"id": "p2", "name": "Bob", "money": 950, "position": 7},
            {"id": "p3", "name": "Charlie", "money": 1500, "position": 2},
        ]
    }

    ui.update_game_state(fake_state)
    ui.display_game_state()

    # In một vài thông báo demo
    time.sleep(1)
    ui.display_message("Alice đã đổ xúc xắc 🎲", "broadcast")
    time.sleep(1)
    ui.display_message("Bob mua được Bất động sản số 8 🏠", "success")
    time.sleep(1)
    ui.display_message("Charlie không đủ tiền để mua!", "error")


🧩 Mục đích:
-------------
- Hiển thị trạng thái game (người chơi, tiền, vị trí, lượt hiện tại)
- In thông báo, lỗi, và chat từ server
- Dọn dẹp console khi cập nhật trạng thái game mới
"""

import os
import time


class MonopolyUI:
    def __init__(self, client=None):
        """
        Khởi tạo UI console cho Monopoly
        :param client: tham chiếu đến MonopolyClient (nếu có)
        """
        self.client = client
        self.game_state = None
        self.player_name = None

    # ----------------------------------------------------------------------
    # 🔧 HÀM CƠ BẢN
    # ----------------------------------------------------------------------
    def set_player_name(self, name: str):
        """Gán tên người chơi hiện tại"""
        self.player_name = name

    def update_game_state(self, state: dict):
        """Cập nhật trạng thái game từ server"""
        self.game_state = state

    def clear_screen(self):
        """Xóa màn hình console"""
        os.system('cls' if os.name == 'nt' else 'clear')

    # ----------------------------------------------------------------------
    # 🎯 HIỂN THỊ TRẠNG THÁI GAME
    # ----------------------------------------------------------------------
    def display_game_state(self):
        """Hiển thị trạng thái hiện tại của bàn cờ"""
        if not self.game_state:
            print("ℹ️ Chưa có thông tin game")
            return

        self.clear_screen()
        print("🎲" * 35)
        print("🎯          MONOPOLY GAME STATE          🎯")
        print("🎲" * 35)
        print()

        # Trạng thái tổng quát
        game_status = self.game_state.get("roomState", "unknown").upper()
        players = self.game_state.get("players", [])
        current_turn_id = self.game_state.get("currentTurn")

        print(f"📊 TRẠNG THÁI PHÒNG: {game_status}")
        print(f"👥 SỐ NGƯỜI CHƠI: {len(players)}")
        print()

        for p in players:
            turn_mark = "⭐" if p.get("id") == current_turn_id else " "
            print(f"{turn_mark} 👤 {p.get('name', '?'):10} | 💰 {p.get('money', 0):6} | 📍 Ô {p.get('position', 0):2}")

        print("=" * 60)
        print("📍 Gõ lệnh: /chat, /roll, /buy, /end, /exit")
        print("=" * 60)

    # ----------------------------------------------------------------------
    # 💬 THÔNG ĐIỆP / CHAT / TRẠNG THÁI
    # ----------------------------------------------------------------------
    def display_message(self, message: str, msg_type: str = "info"):
        """
        Hiển thị thông điệp (từ server hoặc người chơi khác)
        :param message: nội dung thông điệp
        :param msg_type: loại thông báo: info | error | success | warning | broadcast
        """
        icons = {
            "error": "❌",
            "success": "✅",
            "warning": "⚠️",
            "broadcast": "📢",
            "info": "ℹ️"
        }
        print(f"{icons.get(msg_type, '')} {message}")


