import asyncio
import json
import uuid
from typing import Optional, Dict, Callable


class TCPClient:
    def __init__(self, host: str = 'localhost', port: int = 5050):
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.listener_task: Optional[asyncio.Task] = None
        self.message_handlers: Dict[str, Callable] = {}
        self._response_events: Dict[str, asyncio.Event] = {}
        self._response_data: Dict[str, Dict] = {}
        self._pending_requests: Dict[str, str] = {}

    async def connect(self) -> bool:
        if self.connected:
            print("⚠️ Đã kết nối đến server")
            return True
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self.connected = True
            self.listener_task = asyncio.create_task(self._receive_messages())
            print(f"✅ Đã kết nối TCP {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Lỗi kết nối TCP: {e}")
            await self._cleanup()
            return False

    async def send_command(self, command: str, data: Dict = None, timeout: float = 10.0) -> Optional[Dict]:
        if not self.connected or not self.writer:
            print("❌ Chưa kết nối TCP")
            return None
        request_id = str(uuid.uuid4())
        packet = {"cmd": command, "request_id": request_id, "data": data or {}}
        try:
            self.writer.write((json.dumps(packet) + "\n").encode())
            await self.writer.drain()
            print(f"📤 Đã gửi lệnh: {command} ({request_id})")

            if command in ["CREATE_ROOM", "JOIN_ROOM"]:
                return {"status": "PENDING"}

            event = asyncio.Event()
            self._response_events[request_id] = event
            self._pending_requests[request_id] = command

            try:
                await asyncio.wait_for(event.wait(), timeout=timeout)
                return self._response_data.get(request_id)
            except asyncio.TimeoutError:
                print(f"⚠️ Timeout lệnh: {command}")
                return None
            finally:
                self._response_events.pop(request_id, None)
                self._response_data.pop(request_id, None)
                self._pending_requests.pop(request_id, None)
        except Exception as e:
            print(f"❌ Lỗi send_command: {e}")
            return None

    async def _receive_messages(self):
        buffer = ""
        while self.connected and self.reader:
            try:
                data = await asyncio.wait_for(self.reader.read(4096), timeout=1.0)
                if not data:
                    await self._handle_disconnection()
                    break
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    idx = buffer.find('\n')
                    line = buffer[:idx].strip()
                    buffer = buffer[idx + 1:]
                    if line:
                        await self._process_message(line)
            except asyncio.TimeoutError:
                continue
            except (ConnectionResetError, asyncio.CancelledError):
                await self._handle_disconnection()
                break
            except Exception as e:
                print(f"❌ Lỗi TCP receive: {e}")
                await self._handle_disconnection()
                break

    async def _process_message(self, message_str: str):
        try:
            response = json.loads(message_str)
            cmd = response.get("cmd")
            request_id = response.get("request_id")
            print(f"📨 TCP received: {cmd} ({request_id})")

            if cmd in ["ROOM_CREATED", "JOIN_SUCCESS", "ERROR", "PING", "START_GAME", "JOIN_RANDOM_SUCCESS"]:
                handler = self.message_handlers.get(cmd)
                if handler:
                    await handler(response)
                if request_id and request_id in self._response_events:
                    self._response_data[request_id] = response
                    self._response_events[request_id].set()
                return

            if request_id and request_id in self._response_events:
                self._response_data[request_id] = response
                self._response_events[request_id].set()
            elif cmd in self.message_handlers:
                await self.message_handlers[cmd](response)
            else:
                print(f"⚠️ Message không xác định: {cmd}")
        except Exception as e:
            print(f"❌ Lỗi process_message: {e}")

    async def _handle_disconnection(self):
        if not self.connected:
            return
        print("🔌 Mất kết nối TCP, dọn dẹp...")
        self.connected = False
        for event in self._response_events.values():
            event.set()
        await self._cleanup()

    async def _cleanup(self):
        self.connected = False
        if self.listener_task and not self.listener_task.done():
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        self.listener_task = None

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
        self.writer = None
        self.reader = None
        self._response_events.clear()
        self._response_data.clear()
        self._pending_requests.clear()

    def register_handler(self, message_type: str, handler: Callable):
        self.message_handlers[message_type] = handler

    async def disconnect(self):
        await self._cleanup()
        print("🔌 TCP disconnected")
