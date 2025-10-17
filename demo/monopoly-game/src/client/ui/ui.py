# """
# UI hiển thị board và trạng thái game - Phiên bản đầy đủ
# """

# import os
# from typing import Dict, Optional

# class MonopolyUI:
#     def __init__(self, client=None):
#         self.client = client
#         self.game_state = None
#         self.player_name = None
        
#     def set_player_name(self, name: str):
#         """Set tên player hiện tại"""
#         self.player_name = name
        
#     def update_game_state(self, state: dict):
#         """Cập nhật trạng thái game"""
#         self.game_state = state
        
#     def clear_screen(self):
#         """Xóa màn hình console"""
#         os.system('cls' if os.name == 'nt' else 'clear')
        
#     def display_game_state(self):
#         """Hiển thị trạng thái game hiện tại"""
#         if not self.game_state:
#             print("ℹ️ Chưa có thông tin game")
#             return
            
#         self.clear_screen()
        
#         # Header
#         print("🎲" * 35)
#         print("🎯          MONOPOLY GAME STATE          🎯")
#         print("🎲" * 35)
#         print()
        
#         # Game status
#         game_status = self.game_state.get("roomState", "unknown").upper()
#         current_turn_id = self.game_state.get("currentTurn")
#         players = self.game_state.get("players", [])
        
#         status_emoji = {
#             "WAITING": "⏳",
#             "PLAYING": "🎮", 
#             "ENDED": "🏁"
#         }
        
#         print(f"📊 TRẠNG THÁI: {status_emoji.get(game_status, '❓')} {game_status}")
        
#         # Current turn
#         current_player_name = "Unknown"
#         is_my_turn = False
        
#         for player in players:
#             if player.get('id') == current_turn_id:
#                 current_player_name = player.get('name', 'Unknown')
#                 is_my_turn = player.get('name') == self.player_name if self.player_name else False
#                 break
        
#         if is_my_turn:
#             print(f"🎲 LƯỢT CHƠI HIỆN TẠI: 👑 BẠN")
#         else:
#             print(f"🎲 LƯỢT CHƠI HIỆN TẠI: {current_player_name}")
#         print()
        
#         # Players info
#         self.display_players_info()
        
#         print("=" * 60)
#         print("📍 Gõ /help để xem hướng dẫn lệnh")
#         print("=" * 60)
        
#     def display_players_info(self):
#         """Hiển thị thông tin tất cả players"""
#         players = self.game_state.get("players", [])
#         if not players:
#             print("👥 CHƯA CÓ NGƯỜI CHƠI...")
#             return
            
#         print("👥 DANH SÁCH NGƯỜI CHƠI:")
#         print("-" * 50)
        
#         current_turn_id = self.game_state.get("currentTurn")
        
#         for player in players:
#             name = player.get("name", "Unknown")
#             money = player.get("money", 0)
#             position = player.get("position", 0)
#             properties = player.get("properties", [])
#             is_host = player.get("is_host", False)
            
#             # Highlight current player và current turn
#             is_current_player = name.lower() == self.player_name.lower() if self.player_name else False
#             is_current_turn = player.get('id') == current_turn_id
            
#             player_marker = "👑 BẠN" if is_current_player else "👤"
#             host_marker = " 🏠" if is_host else ""
#             turn_marker = " 🎲 (ĐANG CHƠI)" if is_current_turn else ""
            
#             print(f"{player_marker} {name}{host_marker}{turn_marker}")
#             print(f"   💰 ${money:,} | 📍 Vị trí: {position}")
            
#             if properties:
#                 print(f"   🏠 Sở hữu: {len(properties)} property(s)")
#                 if len(properties) <= 3:
#                     prop_list = ", ".join(properties)
#                     print(f"      {prop_list}")
#                 else:
#                     prop_list = ", ".join(properties[:3])
#                     print(f"      {prop_list} ...(+{len(properties)-3})")
#             else:
#                 print(f"   🏠 Chưa có property nào")
#             print()
            
#     def display_message(self, message: str, msg_type: str = "info"):
#         """Hiển thị message từ server"""
#         if msg_type == "error":
#             print(f"❌ {message}")
#         elif msg_type == "success":
#             print(f"✅ {message}")
#         elif msg_type == "warning":
#             print(f"⚠️ {message}")
#         elif msg_type == "broadcast":
#             print(f"📢 {message}")
#         else:
#             print(f"ℹ️ {message}")
            
#     def display_chat(self, sender: str, message: str):
#         """Hiển thị chat message"""
#         print(f"💬 {sender}: {message}")
        
#     def display_game_ended(self, winner: str = None):
#         """Hiển thị khi game kết thúc"""
#         print("\n" + "🎉" * 20)
#         print("🏁          GAME KẾT THÚC!          🏁")
#         print("🎉" * 20)
#         if winner:
#             if winner.lower() == self.player_name.lower() if self.player_name else False:
#                 print(f"🎊 CHÚC MỪNG! Bạn là người thắng cuộc! 🎊")
#             else:
#                 print(f"🎊 Người thắng: {winner}")
#         print("Cảm ơn bạn đã chơi Monopoly!")
#         print("🎉" * 20)



import tkinter as tk
from tkinter import messagebox, ttk
import threading
import json
import socket

# --- CONFIG ---
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007


class MonopolyUI:
    def __init__(self, master):
        self.master = master
        self.master.title("🎲 Monopoly Game Client")
        self.master.geometry("900x600")

        # --- FRAME LAYOUT ---
        self.board_frame = tk.Frame(master, bg="lightgray", width=600, height=600)
        self.info_frame = tk.Frame(master, bg="white", width=300, height=600)

        self.board_frame.pack(side="left", fill="both", expand=True)
        self.info_frame.pack(side="right", fill="y")

        # --- CANVAS for BOARD ---
        self.canvas = tk.Canvas(self.board_frame, bg="#f3f3f3", width=600, height=600)
        self.canvas.pack(fill="both", expand=True)

        # --- INFO PANEL ---
        self.label_turn = tk.Label(self.info_frame, text="Turn: N/A", font=("Arial", 14, "bold"))
        self.label_money = tk.Label(self.info_frame, text="Money: 0", font=("Arial", 12))
        self.log_box = tk.Text(self.info_frame, height=20, state="disabled", bg="#f9f9f9")

        self.label_turn.pack(pady=10)
        self.label_money.pack(pady=5)
        ttk.Separator(self.info_frame, orient="horizontal").pack(fill="x", pady=5)
        tk.Label(self.info_frame, text="Game Log:").pack()
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)

        # --- GAME STATE ---
        self.game_state = {}
        self.tiles = []
        self.player_tokens = {}

        # --- SOCKET LISTENER THREAD ---
        self.listener_thread = threading.Thread(target=self.listen_multicast, daemon=True)
        self.listener_thread.start()

        self.draw_board()

    # ----------------------
    def draw_board(self):
        """Vẽ sơ bộ bàn cờ Monopoly (chỉ là khung vuông và các ô)"""
        size = 10
        tile_size = 50
        self.tiles.clear()
        for i in range(size):
            # Top row
            self.tiles.append(self.canvas.create_rectangle(
                i * tile_size, 0, (i + 1) * tile_size, tile_size, outline="black", fill="white"))
            # Bottom row
            self.tiles.append(self.canvas.create_rectangle(
                i * tile_size, 550, (i + 1) * tile_size, 600, outline="black", fill="white"))
            # Left column
            self.tiles.append(self.canvas.create_rectangle(
                0, i * tile_size, tile_size, (i + 1) * tile_size, outline="black", fill="white"))
            # Right column
            self.tiles.append(self.canvas.create_rectangle(
                550, i * tile_size, 600, (i + 1) * tile_size, outline="black", fill="white"))

    # ----------------------
    def listen_multicast(self):
        """Lắng nghe gói tin từ server (multicast)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', MULTICAST_PORT))

        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        while True:
            data, _ = sock.recvfrom(4096)
            try:
                packet = json.loads(data.decode())
                self.master.after(0, self.update_state, packet)
            except Exception as e:
                print("⚠️ Parse error:", e)

    # ----------------------
    def update_state(self, packet):
        """Cập nhật giao diện dựa vào game state"""
        if packet.get("type") == "state_update":
            self.game_state = packet["state"]
            turn = self.game_state.get("turn")
            money = self.game_state.get("money", {}).get("player1", 0)
            self.label_turn.config(text=f"Turn: {turn}")
            self.label_money.config(text=f"Money: {money}")
            self.add_log(f"🔄 State updated: turn={turn}")

        elif packet.get("type") == "chat":
            msg = packet.get("message", "")
            self.add_log(f"💬 {msg}")

        elif packet.get("type") == "event":
            self.add_log(f"🎯 {packet.get('description')}")

    # ----------------------
    def add_log(self, text):
        """Thêm dòng log vào khung thông báo"""
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.config(state="disabled")
        self.log_box.see("end")


if __name__ == "__main__":
    root = tk.Tk()
    app = MonopolyUI(root)
    root.mainloop()
