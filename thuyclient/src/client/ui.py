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