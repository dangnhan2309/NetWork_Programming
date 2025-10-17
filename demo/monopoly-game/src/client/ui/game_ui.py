import asyncio
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from core.game_client import MonopolyGameClient

from ...server.game.board import Board 

class GameUI:
    def __init__(self, client: 'MonopolyGameClient'):
        self.client = client
        self.game_state: Dict = {}
        self.board = Board() 

    async def update_game_state(self, state_data: Dict):
        if not isinstance(state_data, dict):
            print(f"⚠️ State dữ liệu không hợp lệ: {state_data}")
            return
        state_data.setdefault('players', {})
        state_data.setdefault('current_turn', None)
        state_data.setdefault('round', 1)
        self.game_state = state_data

    async def _get_input(self, prompt: str) -> str:
        """Lấy input từ người dùng"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)
    
    def show_room_help(self):
        """Hiển thị hướng dẫn trong phòng"""
        self.client.menu._show_help()

    async def show_board(self):
        """Hiển thị bàn cờ Monopoly với state thực tế"""
        try:
            if self.game_state:
                self._display_board_with_state()
            else:
                self._display_simple_board()
                
        except Exception as e:
            print(f"❌ Lỗi khi hiển thị board: {e}")
            self._display_simple_board()

    def _display_board_with_state(self):
        """Hiển thị bàn cờ với trạng thái thực tế"""
        players = self.game_state.get('players', {})
        current_turn = self.game_state.get('current_turn')
        round_num = self.game_state.get('round', 1)
        if not players:
            print("⏳ Đang chờ dữ liệu người chơi...")
            return
        
        print(f"\n🎲 BÀN CỜ MONOPOLY - Vòng {round_num}")
        print(f"🎯 Lượt hiện tại: {current_turn}")
        print("=" * 80)
        
        player_positions = {}
        for player_id, player_data in players.items():
            position = player_data.get('position', 0)
            player_name = player_data.get('name', player_id)
            player_positions[player_name] = position
            
            money = player_data.get('money', 0)
            print(f"👤 {player_name}: Ô {position} | 💰 ${money}")
        
        print("=" * 80)
        
        self.board.render_board(player_positions)

    def _display_simple_board(self):
        """Hiển thị bàn cờ đơn giản khi chưa có state"""
        print("\n🎲 BÀN CỜ MONOPOLY (Chế độ xem đơn giản)")
        print("=" * 80)
        self.board.render_board({})

    def show_waiting_room(self, room_id: str, players: list):
        """Hiển thị giao diện phòng chờ"""
        print(f"🎮 ======= PHÒNG CHỜ: {room_id} =======")
        if not players:
            print("👥 Hiện chưa có người chơi nào trong phòng.")
        else:
            print(f"👥 Người chơi trong phòng: {', '.join(players)}")
        print("🕓 Vui lòng chờ chủ phòng bắt đầu trò chơi...\n")

    async def game_loop(self):
        """Vòng lặp game khi đã trong phòng"""
        while self.client.in_room and self.client.running:
            try:
                cmd = await self._get_input("🎮 Lệnh: ")
                cmd = cmd.strip()
                
                if not cmd:
                    continue

                await self.client.command_processor.process_command(cmd)

            except (KeyboardInterrupt, EOFError):
                await self.client.leave_room()
                break
            except Exception as e:
                print(f"❌ Lỗi game loop: {e}")
