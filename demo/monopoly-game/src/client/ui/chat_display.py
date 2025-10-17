import asyncio
from typing import Dict, Optional

class ChatDisplay:
    def __init__(self):
        self._chat_queue = asyncio.Queue()
        self._display_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Bắt đầu hiển thị chat"""
        self._running = True
        self._display_task = asyncio.create_task(self._display_messages())

    async def stop(self):
        """Dừng hiển thị chat"""
        self._running = False
        if self._display_task and not self._display_task.done():
            self._display_task.cancel()
            try:
                await self._display_task
            except asyncio.CancelledError:
                pass

    async def add_message(self, message_data: Dict):
        """Thêm message vào hàng đợi"""
        await self._chat_queue.put(message_data)

    async def _display_messages(self):
        """Hiển thị tin nhắn từ hàng đợi"""
        while self._running:
            try:
                message_data = await asyncio.wait_for(self._chat_queue.get(), timeout=0.1)
                self._print_message(message_data)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    await asyncio.sleep(0.1)

    def _print_message(self, message_data: Dict):
        """In message ra console"""
        msg_type = message_data.get("type")
        
        if msg_type == "SYSTEM":
            print(f"\n📢 [HỆ THỐNG] {message_data['message']}")
            
        elif msg_type == "PLAYER_COUNT":
            print(f"\n👥 Trạng thái phòng: {message_data['player_count']}/{message_data['max_players']} người - {', '.join(message_data['players'])}")
            
        elif msg_type == "PLAYER_JOINED":
            print(f"\n🎉 {message_data['player']} đã tham gia phòng!")
            print(f"👥 Hiện tại: {len(message_data['players'])}/{message_data['max_players']} người: {', '.join(message_data['players'])}")
            
        elif msg_type == "PLAYER_LEFT":
            print(f"\n👋 {message_data['player']} đã rời phòng")
            
        elif msg_type == "GAME_STARTING":
            print(f"\n🚀 Trò chơi đang bắt đầu...")
            
        elif msg_type == "CHAT":
            print(f"\n💬 {message_data['player']}: {message_data['message']}")
            
        elif msg_type == "SELF_CHAT":
            print(f"\n💬 Bạn: {message_data['message']}")
            
        elif msg_type == "DICE_ROLL":
            print(f"\n🎲 {message_data['player']} tung xúc xắc: {message_data['dice_value']}")
            
        elif msg_type == "PLAYER_MOVE":
            print(f"\n📍 {message_data['player']} di chuyển đến ô {message_data['position']}")

        print("🎮 Lệnh: ", end="", flush=True)
