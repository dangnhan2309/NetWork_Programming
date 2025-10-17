import asyncio
import uuid
import datetime
from typing import Optional, Dict

from ..network.tcp_client import TCPClient
from ..network.multicast_client import MulticastClient
from .command_processor import CommandProcessor
from ..ui.menu import MenuManager
from ..ui.game_ui import GameUI
from ..ui.chat_display import ChatDisplay


class MonopolyGameClient:
    def __init__(self, server_host: str = 'localhost', server_port: int = 5050):
        self.tcp_client = TCPClient(server_host, server_port)
        self.multicast_client = MulticastClient()
        self.multicast_client.client = self

        self.menu_manager = MenuManager(self)
        self.game_ui = GameUI(self)
        self.chat_display = ChatDisplay()
        self.command_processor = CommandProcessor(self)

        self.player_name: Optional[str] = None
        self.room_id: Optional[str] = None
        self.is_host = False
        self.connected = False
        self.in_room = False
        self.running = True
        self._game_started = False
        self._max_players = 4
        self.player_position: int = 0
        self._last_displayed_state = None
        self._display_count = 0
        self._last_player_count = 0

        # Đăng ký handler TCP
        self.tcp_client.register_handler("ROOM_CREATED", self.handle_room_created)
        self.tcp_client.register_handler("JOIN_SUCCESS", self.handle_join_success)
        self.tcp_client.register_handler("ROLL_DICE", self.handle_roll_dice_response)
        self.tcp_client.register_handler("GET_GAME_STATE", self.handle_get_game_state_response)
        self.tcp_client.register_handler("ERROR", self.handle_error)

    async def run(self):
        print("🔗 Kết nối server...")
        if not await self.tcp_client.connect():
            print("❌ Không thể kết nối server")
            return
        self.connected = True
        while self.running and self.connected:
            if not self.in_room:
                await self.menu_manager.show_main_menu()
            else:
                await self.game_ui.game_loop()

    async def join_room_success(self, room_id: str, data: dict):
        self.room_id = room_id
        self.in_room = True
        self.is_host = data.get("is_host", False)
        self._max_players = data.get("max_players", 4)
        self._game_started = data.get("game_started", False)
        print(f"🏠 Đã vào phòng {room_id}, host={self.is_host}")

        if self._game_started:
            await self.send_game_command("GET_GAME_STATE")
            if self._last_displayed_state:
                await self.chat_display.show_system_message("🎯 Đồng bộ trạng thái game")

    async def handle_room_created(self, data: Dict):
        room_id = data.get("room_id") or data.get("data", {}).get("room_id")
        if room_id and (not self.in_room or room_id != self.room_id):
            await self.join_room_success(room_id, data.get("data", {}))

    async def handle_join_success(self, data: Dict):
        room_id = data.get("room_id") or data.get("data", {}).get("room_id")
        if room_id and (not self.in_room or room_id != self.room_id):
            await self.join_room_success(room_id, data.get("data", {}))

    async def handle_get_game_state_response(self, data: Dict):
        if data.get("status") == "OK":
            self._last_displayed_state = data.get("data", {})
            await self.game_ui.update_game_state(self._last_displayed_state)
            if not self._game_started:
                self._game_started = True
                await self.game_ui.show_board()

    async def handle_roll_dice_response(self, data: Dict):
        if data.get("status") == "OK":
            dice1 = data["data"].get("dice1", 0)
            dice2 = data["data"].get("dice2", 0)
            new_pos = data["data"].get("new_position", 0)
            self.player_position = new_pos
            print(f"🎲 Dice: {dice1}+{dice2} -> {new_pos}")

    async def send_game_command(self, action: str, args: dict = None, retry_count: int = 1):
        for attempt in range(retry_count + 1):
            response = await self.tcp_client.send_command(action, {"room_id": self.room_id, "player_name": self.player_name, **(args or {})})
            if response:
                if response.get("status") == "OK" and action == "START_GAME":
                    self._game_started = True
                return response
            if attempt < retry_count:
                await asyncio.sleep(1)
        return None

    async def send_chat_message(self, message: str):
        packet = {
            "header": {"room_id": self.room_id, "sender": self.player_name, "type": "EVENT"},
            "command": {"action": "CHAT", "args": {"message": message, "player": self.player_name}},
            "payload": {"message": message}
        }
        await self.multicast_client.send_packet(packet)

    async def handle_error(self, data: Dict):
        print(f"❌ Error từ server: {data.get('message', 'Unknown')}")

    async def _cleanup_room(self):
        self.in_room = False
        self._game_started = False
        self.is_host = False
        self.room_id = None
        await self.chat_display.stop()
        await self.multicast_client.leave_multicast_group()
        print("🚪 Rời phòng")

    async def cleanup(self):
        self.running = False
        if self.in_room:
            await self._cleanup_room()
        await self.tcp_client.disconnect()
        await self.chat_display.stop()
        print("✅ Client cleanup xong")
