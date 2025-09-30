
import asyncio
import json
import websockets

from ..shared.protocol import Protocol
from ..shared.Command_list import command_dic
from .ui import ClientUI


class Client:
    def __init__(self, uri="ws://localhost:8765", name="Guest"):
        self.uri = uri
        self.name = name
        self.ui = ClientUI()   # Khởi tạo UI

    async def run(self):
        """
           Attempts to connect to a WebSocket server and prints a log message.

           Args:
           """
        try:
            async with websockets.connect(self.uri) as websocket:
                print(f"[CLIENT] Connected to {self.uri} as {self.name}")
                await websocket.send("Hello Client")
                await asyncio.gather(
                    self.user_input_loop(websocket),
                    self.receive_message(websocket),
                )
        except Exception as e :
            print("")

    async def user_input_loop(self, websocket):
        """
        CLI loop cho người chơi nhập lệnh.
        Có thể nhập CHAT, JOIN hoặc chọn command trong command_dic.
        """
        while True:
            raw = await asyncio.to_thread(input, f"{self.name}> ")
            #self.ui.update_map()
            if raw.startswith("TC"):
                pass

            if raw.startswith("CHAT "):
                # Ví dụ: CHAT hello
                msg = raw[5:]
                await self.send_command(websocket, "CHAT", {"message": msg})
                continue

            if raw.startswith("JOIN "):
                # Ví dụ: JOIN Nhan
                nick = raw[5:]
                await self.send_command(websocket, "JOIN", {"name": nick})
                continue

            if raw in command_dic:
                await self.send_command(websocket, raw)
                continue

            print(f"[CLIENT] Unknown input: {raw}")

    async def send_command(self, websocket, key: str, overrides: dict = None):
        """Gửi lệnh Monopoly từ command_dic."""
        if key not in command_dic:
            print(f"[ERROR] Command {key} not found in command_dic")
            return

        # Copy object để không ảnh hưởng đến bản gốc
        msg = json.loads(json.dumps(command_dic[key]))

        if overrides:
            msg["data"].update(overrides)

        packet = Protocol.make_packet(msg["action"], msg["data"])
        await websocket.send(packet)
        print(f"[CLIENT] Sent -> {msg}")

    async def receive_message(self, websocket):
        """Nhận và xử lý message từ server."""
        async for message in websocket:
            packet = Protocol.parse_packet(message)
            action = packet.get("action")
            data = packet.get("data", {})

            print(f"\n[SERVER] {action} {data}")

            # ==== Dùng UI để hiển thị ====
            if action == "GAME_STATE":

                self.ui.update_map(data)
                # hiển thị menu nếu có command gợi ý
                if "available_commands" in data:
                    self.ui.display_commands(data["available_commands"])

            elif action == "ROLL_RESULT":
                print(f"🎲 Dice Result: {data.get('dice', '?')}")

            elif action == "CHAT":
                print(f"[CHAT] {data.get('message')}")

            elif action == "PLAYER_STATUS":
                pid = data.get("player_id", "Unknown")
                status = data.get("status", {})
                self.ui.update_player_status(pid, status)

            elif action == "PROPERTIES":
                self.ui.show_properties(data.get("properties", []))

            elif action == "ERROR":
                print(f"❌ Error: {data.get('msg')}")

            # Prompt lại cho user
            print(f"{self.name}> ", end="", flush=True)


if __name__ == "__main__":
    client = Client(uri="ws://localhost:8765", name="Alice")
    asyncio.run(client.run())

