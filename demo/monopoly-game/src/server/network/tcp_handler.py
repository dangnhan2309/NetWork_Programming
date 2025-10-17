"""Xử lý kết nối TCP từ client"""
import json
import asyncio
import random
from datetime import datetime, timezone
from typing import Dict, Optional, Callable, List
from ..rooms.room_manager import RoomManager
from ..utils.logger import Logger
from ..utils.formatters import ServerFormatter

class TCPHandler:
    """Xử lý kết nối TCP từ client"""

    def __init__(self, room_manager, game_manager, logger: Logger, multicast_manager=None):
        self.room_manager = room_manager
        self.game_manager = game_manager
        self.logger = logger
        self.formatter = ServerFormatter()
        self.connected_clients = set() # Chứa các writer objects
        self.broadcast_callback: Optional[Callable] = None
        self.multicast_manager = multicast_manager
        # Mapping player_name -> writer để gửi tin nhắn trực tiếp qua TCP (nếu cần)
        self.player_to_writer: Dict[str, asyncio.StreamWriter] = {} 

    def set_broadcast_callback(self, callback: Callable):
        """Thiết lập callback để broadcast message (thường là để gửi cho toàn bộ server hoặc phòng)"""
        self.broadcast_callback = callback
    
    # --- Hàm tiện ích cho TCP/Messaging ---
    
    async def send_response(self, writer: asyncio.StreamWriter, response: Dict):
        """Gửi phản hồi JSON qua TCP"""
        try:
            message = json.dumps(response) + '\n' # Thêm ký tự xuống dòng để phân biệt message
            writer.write(message.encode())
            await writer.drain()
            self.logger.debug(f"⬅️ Gửi {len(message.encode())} bytes về {writer.get_extra_info('peername')}")
        except Exception as e:
            self.logger.error(f"❌ Lỗi gửi phản hồi TCP: {e}")
            
    async def send_to_room(self, room_id: str, message: Dict, exclude_writer: Optional[asyncio.StreamWriter] = None):
        """Gửi tin nhắn (JSON dict) đến tất cả client trong phòng qua TCP/Multicast"""
        # Ưu tiên Multicast nếu có và phòng đang active
        if self.multicast_manager and self.multicast_manager.is_room_active(room_id):
            # Gửi qua Multicast (giả định Multicast Manager sẽ định dạng message)
            try:
                # Tạo packet đơn giản để multicast (giả định client sẽ nhận được)
                mc_packet = {
                    "header": {"room_id": room_id, "sender": "SERVER", "type": "COMMAND_BROADCAST", 
                               "timestamp": datetime.now(timezone.utc).isoformat()},
                    "command": {"action": message.get("cmd", "UPDATE")},
                    "payload": message
                }
                await self.multicast_manager.broadcast_to_room(room_id, mc_packet)
                self.logger.debug(f"📻 Multicast broadcasted {message.get('cmd')} to {room_id}")
                return
            except Exception as e:
                self.logger.error(f"❌ Lỗi Multicast broadcast: {e}. Falling back to TCP...")

        # Fallback to TCP (chỉ gửi cho những người đang kết nối qua TCP/Player_to_Writer)
        room_info = self.room_manager.get_room_info(room_id)
        if room_info:
            player_names = room_info.get('players', [])
            for player_name in player_names:
                writer = self.player_to_writer.get(player_name)
                if writer and writer in self.connected_clients and writer != exclude_writer:
                    await self.send_response(writer, message)
    
    async def cleanup_client(self, client_info: Dict, connection_type: str):
        """Đóng kết nối và dọn dẹp (rời phòng, xóa khỏi danh sách)"""
        writer = client_info['writer']
        player_name = client_info.get('player_name')
        room_id = client_info.get('room_id')
        addr = client_info['addr']
        
        # 1. Xóa khỏi danh sách client
        if writer in self.connected_clients:
            self.connected_clients.remove(writer)
            
        # 2. Xóa khỏi player_to_writer mapping
        if player_name and self.player_to_writer.get(player_name) == writer:
            del self.player_to_writer[player_name]

        # 3. Xử lý rời phòng
        if room_id and player_name:
            # Rời phòng trong RoomManager
            await self.room_manager.remove_player(room_id, player_name)
            self.logger.info(f"🚪 {player_name} đã rời phòng {room_id} do mất kết nối.")
            
            # Broadcast thông báo cho những người còn lại
            if self.broadcast_callback:
                await self.broadcast_callback(room_id, f"🚨 {player_name} đã ngắt kết nối/rời phòng!")
        
        # 4. Đóng kết nối
        try:
            self.logger.info(f"🚫 [HỆ THỐNG] Ngắt kết nối với {addr[0]}:{addr[1]}")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            self.logger.error(f"❌ Lỗi đóng kết nối: {e}")

    async def start_game_if_ready(self, room_id: str):
        """Tự động bắt đầu game khi đủ người"""
        try:
            room_info = self.room_manager.get_room_info(room_id)
            if not room_info:
                self.logger.warning(f"⚠️ Không tìm thấy room {room_id}")
                return

            player_count = len(room_info.get('players', []))
            max_players = room_info.get('max_players', 2)
            self.logger.info(f"👥 Room {room_id} có {player_count}/{max_players} người chơi")

            if player_count < max_players:
                self.logger.info(f"⌛ Chưa đủ người để bắt đầu game trong {room_id}")
                return

            if room_info.get('game_started', False):
                self.logger.info(f"✅ Game trong {room_id} đã bắt đầu trước đó.")
                return

            # ✅ Cập nhật trạng thái phòng
            await self.room_manager.start_game(room_id)
            self.logger.info(f"🎮 Game started for room {room_id}")

            # ✅ Khởi tạo game logic
            self.game_manager.initialize_game(room_id, room_info['players'])

            # ✅ Gửi thông báo đến tất cả client trong phòng
            start_msg = {
                "cmd": "GAME_STARTED",
                "status": "OK",
                "data": {
                    "room_id": room_id,
                    "players": room_info['players'],
                    "message": f"Trò chơi trong phòng '{room_info['room_name']}' đã bắt đầu!"
                }
            }
            await self.send_to_room(room_id, start_msg)

            # ✅ Broadcast hệ thống nếu cần
            if self.broadcast_callback:
                await self.broadcast_callback(room_id, "🎮 TRÒ CHƠI ĐÃ BẮT ĐẦU TỰ ĐỘNG!")

            self.logger.info(f"🚀 Auto-started game in {room_id} (players: {player_count})")

        except Exception as e:
            self.logger.error(f"❌ Lỗi auto start game: {e}")

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Xử lý kết nối TCP từ client"""
        try:
            addr = writer.get_extra_info('peername')
            self.logger.info(f"📢 [HỆ THỐNG] Kết nối mới từ {addr[0]}:{addr[1]}")

            client_info = {
                'reader': reader,
                'writer': writer,
                'addr': addr,
                'player_name': None,
                'room_id': None
            }
            self.connected_clients.add(writer)

            while True:
                data = await reader.read(1024)
                if not data:
                    break

                message = data.decode().strip()
                self.logger.debug(f"📨 Nhận {len(message)} bytes từ {addr[0]}")

                try:
                    msg_dict = json.loads(message)
                    cmd = msg_dict.get('cmd')
                    request_id = msg_dict.get('request_id')

                    if 'player_name' in msg_dict.get('data', {}):
                        player_name = msg_dict['data']['player_name']
                        client_info['player_name'] = player_name
                        self.player_to_writer[player_name] = writer

                    if cmd == "PING":
                        pong_response = {
                            'cmd': 'PONG',
                            'status': 'OK',
                            'request_id': request_id,
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        await self.send_response(writer, pong_response)
                        continue

                    response = await self.handle_command(cmd, msg_dict.get('data', {}), client_info, "TCP")
                    if response:
                        await self.send_response(writer, response)

                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ Không thể parse JSON từ {addr[0]}: {message}")
                    error_response = {
                        'cmd': 'ERROR',
                        'status': 'ERROR',
                        'message': 'Định dạng JSON không hợp lệ'
                    }
                    await self.send_response(writer, error_response)

        except ConnectionResetError:
            self.logger.warning(f"⚠️ Mất kết nối đột ngột với {addr[0] if 'addr' in locals() else 'unknown'}")
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý client {addr[0] if 'addr' in locals() else 'unknown'}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if 'client_info' in locals():
                await self.cleanup_client(client_info, "TCP")

    async def process_single_message(self, message_str: str, client_info: dict, connection_type: str):
        """Xử lý một message JSON (Có thể dùng cho Websocket/Multicast Receiver)"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            data = json.loads(message_str)
            cmd = data.get("cmd")
            payload = data.get("data", {})
            
            self.logger.info(f"📨 Nhận từ {connection_type}: {cmd}")

            if 'player_name' in payload:
                client_info['player_name'] = payload['player_name']
                # Cập nhật mapping nếu có writer
                if 'writer' in client_info:
                    self.player_to_writer[payload['player_name']] = client_info['writer']

            response = await self.handle_command(cmd, payload, client_info, connection_type)
            
            if response and 'writer' in client_info:
                await self.send_response(client_info['writer'], response)
                
        except json.JSONDecodeError as e:
            self.logger.error(self.formatter.format_error("JSON", str(e)))
            error_response = {
                "cmd": "ERROR", 
                "status": "ERROR", 
                "message": "Định dạng JSON không hợp lệ"
            }
            if 'writer' in client_info:
                await self.send_response(client_info['writer'], error_response)
        except Exception as e:
            self.logger.error(self.formatter.format_error("Xử lý message", str(e)))
            error_response = {
                "cmd": "ERROR", 
                "status": "ERROR", 
                "message": "Lỗi server nội bộ"
            }
            if 'writer' in client_info:
                await self.send_response(client_info['writer'], error_response)

    async def handle_command(self, cmd: str, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý command từ client"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        handlers = {
            "LIST_ROOMS": self.handle_list_rooms,
            "JOIN_RANDOM": self.handle_join_random,
            "CREATE_ROOM": self.handle_create_room,
            "JOIN_ROOM": self.handle_join_room,
            "LEAVE_ROOM": self.handle_leave_room,
            "START_GAME": self.handle_start_game,
            "GET_BOARD": self.handle_get_board,
            "ROLL_DICE": self.handle_roll_dice,
            "BUY_PROPERTY": self.handle_buy_property,
            "END_TURN": self.handle_end_turn,          # <-- Đã thêm
            "CHAT": self.handle_chat,                  # <-- Đã thêm
            "GET_PLAYER_INFO": self.handle_get_player_info, # <-- Đã thêm
            "GET_GAME_STATE": self.handle_get_game_state,   # <-- Đã thêm
            "PONG": self.handle_pong                   # <-- Đã thêm
        }
        
        handler = handlers.get(cmd)
        if handler:
            return await handler(payload, client_info, connection_type)
        else:
            return {
                "cmd": "ERROR", 
                "status": "ERROR", 
                "message": f"Lệnh không hợp lệ: {cmd}"
            }

    # --- Các hàm xử lý game/phòng (Bạn đã cung cấp) ---
    async def handle_list_rooms(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý lệnh LIST_ROOMS"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            rooms = await self.room_manager.list_rooms()
            return {
                "cmd": "ROOM_LIST", 
                "data": rooms, 
                "status": "OK",
                "message": f"Tìm thấy {len(rooms)} phòng"
            }
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy danh sách phòng: {e}")
            return {
                "cmd": "ROOM_LIST", 
                "status": "ERROR", 
                "message": "Không thể lấy danh sách phòng"
            }

    async def handle_join_random(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý tham gia phòng ngẫu nhiên"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            player_name = payload.get("player_name", f"Player_{client_info['addr'][1]}")
            client_info['player_name'] = player_name
            
            self.logger.info(self.formatter.format_system_message(f"{player_name} đang tìm phòng ngẫu nhiên..."))
            
            # Tìm phòng có sẵn phù hợp
            best_room_id = await self.room_manager.find_best_room(player_name)
            
            if best_room_id:
                room_info = await self.room_manager.add_player(best_room_id, player_name)
                if room_info:
                    client_info['room_id'] = best_room_id
                    
                    self.logger.info(self.formatter.format_player_join(
                        player_name, room_info['room_name'], 
                        len(room_info['players']), room_info['max_players']
                    ))
                    
                    # Broadcast thông báo
                    if self.broadcast_callback:
                        await self.broadcast_callback(
                            best_room_id,
                            f"🎊 {player_name} đã tham gia phòng! ({len(room_info['players'])}/{room_info['max_players']} người)"
                        )
                    
                    # Kiểm tra và bắt đầu game nếu đủ người
                    if self.room_manager.can_start_game(best_room_id):
                        await self.start_game_if_ready(best_room_id)
                    
                    return {
                        "cmd": "JOIN_SUCCESS", 
                        "status": "OK",
                        "data": room_info,
                        "message": f"Đã tham gia '{room_info['room_name']}' thành công!",
                        "join_type": "EXISTING_ROOM"
                    }
            
            # Tạo phòng mới nếu không tìm thấy
            self.logger.info(self.formatter.format_system_message(f"Không tìm thấy phòng phù hợp, đang tạo phòng mới cho {player_name}..."))
            room_data = await self.room_manager.auto_create_room(player_name)
            
            if room_data:
                client_info['room_id'] = room_data['room_id']
                room_info = await self.room_manager.add_player(room_data['room_id'], player_name)
                
                self.logger.info(self.formatter.format_room_created(
                    room_data['room_name'], player_name, room_data['max_players']
                ))
                
                # 🔥 TẠO MULTICAST SOCKET CHO PHÒNG MỚI (nếu chưa có)
                if self.multicast_manager:
                    multicast_ip = room_data["multicast_ip"]
                    port = room_data["port"]
                    try:
                        self.multicast_manager.create_group(room_data['room_id'], multicast_ip, port)
                        self.logger.info(f"✅ Multicast socket created for {room_data['room_id']}")
                    except Exception as e:
                        self.logger.error(f"❌ Error creating multicast socket: {e}")

                if self.broadcast_callback:
                    await self.broadcast_callback(
                        room_data['room_id'],
                        f"🏠 Phòng '{room_data['room_name']}' đã được tạo tự động! Chờ người chơi khác..."
                    )
                
                return {
                    "cmd": "JOIN_SUCCESS", 
                    "status": "OK",
                    "data": room_info,
                    "message": f"Đã tạo và tham gia '{room_data['room_name']}' thành công!",
                    "join_type": "NEW_ROOM"
                }
            
            return {
                "cmd": "JOIN_SUCCESS", 
                "status": "ERROR", 
                "message": "Không thể tìm hoặc tạo phòng phù hợp"
            }
            
        except Exception as e:
            self.logger.error(self.formatter.format_error("Tham gia phòng ngẫu nhiên", str(e)))
            return {
                "cmd": "JOIN_SUCCESS", 
                "status": "ERROR", 
                "message": "Lỗi khi tham gia phòng ngẫu nhiên"
            }

    async def handle_create_room(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý tạo phòng mới - TẠO MULTICAST SOCKET NGAY"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            room_name = payload.get("room_name", f"Room-{len(self.room_manager.rooms)}")
            player_name = payload.get("player_name", "UnknownPlayer")
            max_players = payload.get("max_players", 4)
            
            # Tạo room ID
            room_id = f"ROOM_{len(self.room_manager.rooms)}_{id(client_info['writer'])}"
            
            self.logger.info(f"🏠 {player_name} đang tạo phòng: {room_name}")
            
            # Tạo phòng
            room_info = await self.room_manager.create_room(
                room_id=room_id,
                room_name=room_name,
                host_name=player_name,
                max_players=max_players
            )

            if room_info:
                client_info['player_name'] = player_name
                client_info['room_id'] = room_id
                
                # 🔥 QUAN TRỌNG: TẠO MULTICAST SOCKET NGAY KHI TẠO PHÒNG
                if self.multicast_manager:
                    multicast_ip = room_info["multicast_ip"]
                    port = room_info["port"]
                    
                    self.logger.info(f"🔧 Creating multicast socket for {room_id} at {multicast_ip}:{port}")
                    
                    try:
                        # Tạo multicast socket
                        group_info = self.multicast_manager.create_group(room_id, multicast_ip, port)
                        if group_info:
                            self.logger.info(f"✅ Multicast socket created for {room_id}")
                        else:
                            self.logger.error(f"❌ Failed to create multicast socket for {room_id}")
                    except Exception as e:
                        self.logger.error(f"❌ Error creating multicast socket: {e}")
                else:
                    self.logger.warning(f"⚠️ No multicast manager available for {room_id}")
                
                # Đảm bảo room_info có đầy đủ thông tin
                room_info['host_name'] = player_name
                room_info['is_host'] = True
                
                self.logger.info(f"✅ Room created: {room_name}, Host: {player_name}")
                
                if self.broadcast_callback:
                    await self.broadcast_callback(
                        room_id,
                        f"🎮 Phòng '{room_name}' đã được tạo bởi {player_name}"
                    )
                
                return {
                    "cmd": "ROOM_CREATED",
                    "data": room_info,
                    "status": "OK",
                    "message": f"Đã tạo phòng '{room_name}' thành công!"
                }
            else:
                return {
                    "cmd": "ROOM_CREATED",
                    "status": "ERROR",
                    "message": "Không thể tạo phòng"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi tạo phòng: {e}")
            return {
                "cmd": "ROOM_CREATED",
                "status": "ERROR",
                "message": "Lỗi khi tạo phòng"
            }

    async def handle_join_room(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý tham gia phòng cụ thể - ĐÃ SỬA HOST INFO"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            room_id = payload.get("room_id")
            player_name = payload.get("player_name", f"Player_{client_info['addr'][1]}")
            
            if not room_id:
                return {
                    "cmd": "JOIN_SUCCESS", 
                    "status": "ERROR", 
                    "message": "Vui lòng cung cấp mã phòng"
                }
            
            client_info['player_name'] = player_name
            
            # Rời phòng cũ nếu có
            old_room_id = client_info.get('room_id')
            if old_room_id and old_room_id != room_id:
                await self.room_manager.remove_player(old_room_id, player_name)
                if self.broadcast_callback:
                    await self.broadcast_callback(old_room_id, f"👋 {player_name} đã rời phòng")
            
            if room_id in self.room_manager.rooms:
                room_info = await self.room_manager.add_player(room_id, player_name)
                if room_info:
                    client_info['room_id'] = room_id

                    is_host = (room_info.get('host_name') == player_name)
                    room_info['is_host'] = is_host

                    # SETUP MULTICAST KHI JOIN PHÒNG (Đảm bảo group đã được tạo)
                    if self.multicast_manager:
                        multicast_ip = room_info.get("multicast_ip")
                        port = room_info.get("port")
                        if multicast_ip and port:
                             self.multicast_manager.create_group(room_id, multicast_ip, port) # Đảm bảo group tồn tại
                             self.logger.info(f"✅ Multicast group confirmed/created for {room_id}")

                    if room_info.get('game_started', False):
                        if not self.game_manager.is_player_in_game(room_id, player_name):
                            self.game_manager.add_player_to_game(room_id, player_name)

                    self.logger.info(f"🎉 {player_name} tham gia phòng: {room_info['room_name']} - Host: {is_host}")
                    if self.broadcast_callback:
                        await self.broadcast_callback(
                            room_id,
                            f"🎊 {player_name} đã tham gia phòng! ({len(room_info['players'])}/{room_info['max_players']} người)"
                        )
                    
                    # Kiểm tra và bắt đầu game nếu đủ người
                    if self.room_manager.can_start_game(room_id):
                        await self.start_game_if_ready(room_id)
                    
                    return {
                        "cmd": "JOIN_SUCCESS", 
                        "status": "OK",
                        "data": room_info,
                        "message": f"Đã tham gia phòng '{room_info['room_name']}' thành công!"
                    }
                else:
                    return {
                        "cmd": "JOIN_SUCCESS", 
                        "status": "ERROR", 
                        "message": "Phòng đã đầy hoặc có lỗi xảy ra"
                    }
            else:
                rooms = await self.room_manager.list_rooms()
                available_rooms = list(rooms.keys())
                return {
                    "cmd": "ERROR", 
                    "status": "ERROR", 
                    "message": f"Không tìm thấy phòng '{room_id}'. Các phòng có sẵn: {', '.join(available_rooms[:3])}..."
                }
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi tham gia phòng: {e}")
            return {
                "cmd": "JOIN_SUCCESS", 
                "status": "ERROR", 
                "message": "Lỗi khi tham gia phòng"
            }

    async def handle_leave_room(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý rời phòng"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            room_id = payload.get("room_id") or client_info.get('room_id')
            player_name = payload.get("player_name") or client_info.get('player_name')
            
            if room_id and player_name:
                success = await self.room_manager.remove_player(room_id, player_name)
                
                if success:
                    client_info['room_id'] = None
                    
                    if self.broadcast_callback:
                        await self.broadcast_callback(room_id, f"👋 {player_name} đã rời phòng")
                    
                    return {
                        "cmd": "LEAVE_RESULT", 
                        "status": "OK",
                        "message": "Đã rời phòng thành công"
                    }
            
            return {
                "cmd": "LEAVE_RESULT", 
                "status": "ERROR", 
                "message": "Lỗi khi rời phòng (Phòng hoặc tên người chơi không hợp lệ)"
            }
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi rời phòng: {e}")
            return {
                "cmd": "LEAVE_RESULT", 
                "status": "ERROR", 
                "message": "Lỗi khi rời phòng"
            }

    async def broadcast_game_state(self, room_id: str):
        """Broadcast game state qua multicast hoặc TCP"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            game_state = self.game_manager.get_game_state(room_id)
            if not game_state:
                self.logger.warning(f"⚠️ Không thể lấy game state cho phòng {room_id}")
                return

            state_update_msg = {
                "cmd": "STATE_UPDATE",
                "status": "OK",
                "data": game_state,
                "message": "Cập nhật trạng thái game"
            }
            
            # Gửi qua Multicast (Ưu tiên)
            if self.multicast_manager and self.multicast_manager.is_room_active(room_id):
                mc_packet = {
                    "header": {
                        "room_id": room_id,
                        "sender": "SERVER",
                        "type": "STATE",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    "command": {
                        "action": "STATE_UPDATE"
                    },
                    "payload": {
                        "data": game_state
                    }
                }
                await self.multicast_manager.broadcast_to_room(room_id, mc_packet)
                self.logger.debug(f"📻 Multicast broadcasted STATE_UPDATE to {room_id}")
            
            # Gửi qua TCP cho tất cả client trong phòng (Fallback/TCP-Only)
            await self.send_to_room(room_id, state_update_msg) 

        except Exception as e:
            self.logger.error(f"❌ Lỗi broadcast game state: {e}")
            

    async def handle_start_game(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý bắt đầu game - ĐÃ SỬA ĐỂ KHỞI TẠO STATE VÀ XỬ LÝ RESPONSE CHÍNH XÁC"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            room_id = payload.get("room_id") or client_info.get('room_id')
            player_name = payload.get("player_name") or client_info.get('player_name')
            
            if not room_id:
                return {"cmd": "START_GAME", "status": "ERROR", "message": "Bạn chưa tham gia phòng nào"}
            
            room_info = self.room_manager.get_room_info(room_id)
            if not room_info:
                return {"cmd": "START_GAME", "status": "ERROR", "message": "Không tìm thấy thông tin phòng"}
            
            # 🔥 Kiểm tra game đã bắt đầu (TRẢ VỀ OK ĐỂ TRÁNH TIMEOUT)
            if room_info.get('game_started', False):
                return {
                    "cmd": "START_GAME", 
                    "status": "OK", 
                    "message": "Game đã được bắt đầu trước đó! (tự động khi đủ người)",
                    "data": {"already_started": True, "room_id": room_id}
                }
            
            # Kiểm tra quyền host
            if room_info.get('host_name') != player_name:
                return {"cmd": "START_GAME", "status": "ERROR", "message": "Chỉ chủ phòng mới có thể bắt đầu game"}
            
            # Kiểm tra số lượng người chơi (có thể được xử lý trong room_manager.start_game)
            if len(room_info.get('players', [])) < 2:
                return {"cmd": "START_GAME", "status": "ERROR", "message": "Cần ít nhất 2 người chơi để bắt đầu game"}
            
            
            # 🔥 BƯỚC QUAN TRỌNG: KHỞI TẠO GAME STATE Ở ĐÂY
            # Lỗi 'player_name is not defined' xảy ra trong get_initial_state_for_room/initialize_game
            # Sau khi sửa lỗi này trong module Game Manager, code này sẽ chạy đúng:
            initial_state = None
            if hasattr(self.game_manager, 'get_initial_state_for_room'):
                 self.logger.info(f"🚀 Đang khởi tạo game state cho phòng {room_id}...")
                 # Giả định game_manager.get_initial_state_for_room tồn tại và hoạt động
                 initial_state = await self.game_manager.get_initial_state_for_room(room_id, room_info['players'])
            else:
                 self.logger.error("Server thiếu module Game Manager/Session để khởi tạo state.")
                 
            # 🔥 GỌI ROOM MANAGER VÀ XỬ LÝ KẾT QUẢ DICT
            result = await self.room_manager.start_game(room_id, initial_state=initial_state)

            if result["success"]:
                # Game khởi động thành công
                if self.broadcast_callback:
                    await self.broadcast_callback(room_id, f"🎮 TRÒ CHƠI ĐÃ BẮT ĐẦU! (Game State khởi tạo: {initial_state is not None})")
                
                # Broadcas state đầu tiên
                await self.broadcast_game_state(room_id)

                return {
                    "cmd": "START_GAME", 
                    "status": "OK",
                    "message": result["message"], # Dùng message từ RoomManager (Đã bắt đầu thành công!)
                    "data": {
                        "room_id": room_id, 
                        "players": room_info['players'],
                        "already_started": False 
                    }
                }
            else:
                # Game không thể bắt đầu (chưa đủ người/lỗi khác)
                return {
                    "cmd": "START_GAME", 
                    "status": "ERROR", 
                    "message": result["message"] # Dùng message từ RoomManager (Chưa đủ người chơi...)
                }
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi nghiêm trọng khi xử lý START_GAME: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                "cmd": "START_GAME", 
                "status": "ERROR", 
                "message": f"Lỗi Server nội bộ khi bắt đầu game: {e}"
            }

    async def handle_get_board(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý lấy thông tin bàn cờ"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            room_id = client_info.get('room_id')
            
            if not room_id:
                return {
                    "cmd": "GET_BOARD", 
                    "status": "ERROR", 
                    "message": "Bạn chưa tham gia phòng nào"
                }
            
            board_display = self.game_manager.display_board(room_id)
            
            return {
                "cmd": "GET_BOARD", 
                "status": "OK",
                "data": {
                    "board": board_display,
                    "room_id": room_id
                },
                "message": "Đã lấy thông tin bàn cờ thành công"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy bàn cờ: {e}")
            return {
                "cmd": "GET_BOARD", 
                "status": "ERROR", 
                "message": "Lỗi khi lấy thông tin bàn cờ"
            }

    async def handle_roll_dice(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý tung xúc xắc - ĐÃ SỬA LỖI CRASH"""
        # ... (Phần code này giống hệt như bạn đã cung cấp) ...
        try:
            room_id = client_info.get('room_id')
            player_name = client_info.get('player_name')
            
            if not room_id or not player_name:
                 return {
                    "cmd": "ROLL_DICE", 
                    "status": "ERROR", 
                    "message": "Bạn chưa tham gia phòng nào hoặc thiếu tên người chơi"
                }
            
            # Kiểm tra game đã bắt đầu chưa
            room_info = self.room_manager.get_room_info(room_id)
            if not room_info or not room_info.get('game_started', False):
                return {
                    "cmd": "ROLL_DICE", 
                    "status": "ERROR", 
                    "message": "Game chưa bắt đầu"
                }
            
            # Kiểm tra lượt của người chơi
            if not self.game_manager.is_player_turn(room_id, player_name):
                current_turn = self.game_manager.get_current_turn_player(room_id)
                return {
                    "cmd": "ROLL_DICE", 
                    "status": "ERROR", 
                    "message": f"Chưa đến lượt của bạn. Lượt của: {current_turn}"
                }
            
            # 🔥 SỬA: Sử dụng game_manager thay vì game_session trực tiếp
            dice_result = self.game_manager.roll_dice(room_id, player_name)
            
            if dice_result and dice_result.get('success', False):
                dice1 = dice_result.get('dice1', 0)
                dice2 = dice_result.get('dice2', 0)
                total = dice1 + dice2
                new_position = dice_result.get('new_position', 0)
                
                # Broadcast kết quả
                if self.broadcast_callback:
                    await self.broadcast_callback(
                        room_id,
                        f"🎲 {player_name} tung xúc xắc: {dice1} + {dice2} = {total} → Đến ô {new_position}"
                    )
                
                # 🔥 THÊM: Broadcast state update
                await self.broadcast_game_state(room_id)
                
                return {
                    "cmd": "ROLL_DICE", 
                    "status": "OK",
                    "data": {
                        "dice1": dice1,
                        "dice2": dice2,
                        "total": total,
                        "player": player_name,
                        "new_position": new_position,
                        "tile_info": dice_result.get('tile_info', {})
                    },
                    "message": f"Tung xúc xắc: {dice1} + {dice2} = {total}. {dice_result.get('action_message', '')}"
                }
            else:
                return {
                    "cmd": "ROLL_DICE", 
                    "status": "ERROR", 
                    "message": dice_result.get('message', 'Lỗi khi tung xúc xắc')
                }
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi tung xúc xắc: {e}")
            import traceback
            traceback.print_exc()
            return {
                "cmd": "ROLL_DICE", 
                "status": "ERROR", 
                "message": "Lỗi server khi tung xúc xắc"
            }

    async def handle_buy_property(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý mua tài sản"""
        # ... (Phần code bạn đã cung cấp, được tiếp tục)
        try:
            room_id = client_info.get('room_id')
            player_name = client_info.get('player_name')
            property_id = payload.get("property_id")
            
            if not room_id or not player_name:
                return {
                    "cmd": "BUY_PROPERTY", 
                    "status": "ERROR", 
                    "message": "Bạn chưa tham gia phòng nào"
                }
            
            if not property_id:
                return {
                    "cmd": "BUY_PROPERTY", 
                    "status": "ERROR", 
                    "message": "Thiếu mã tài sản (property_id)"
                }
            
            # Thực hiện mua tài sản
            buy_result = self.game_manager.buy_property(room_id, player_name, property_id)
            success = buy_result.get("success", False)
            message = buy_result.get("message", "Lỗi không xác định")
            
            if success:
                if self.broadcast_callback:
                    await self.broadcast_callback(
                        room_id,
                        f"🏠 {player_name} đã mua {buy_result.get('property_name', property_id)} với giá {buy_result.get('cost', '???')}!"
                    )
                
                # Broadcast state update
                await self.broadcast_game_state(room_id)

                return {
                    "cmd": "BUY_PROPERTY", 
                    "status": "OK",
                    "data": buy_result,
                    "message": message
                }
            else:
                return {
                    "cmd": "BUY_PROPERTY", 
                    "status": "ERROR", 
                    "message": message
                }
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi mua tài sản: {e}")
            return {
                "cmd": "BUY_PROPERTY", 
                "status": "ERROR", 
                "message": "Lỗi server khi mua tài sản"
            }
        
    # --- Các hàm xử lý game logic còn thiếu ---
    
    async def handle_end_turn(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý kết thúc lượt chơi"""
        try:
            room_id = client_info.get('room_id')
            player_name = client_info.get('player_name')

            if not room_id or not player_name:
                return {"cmd": "END_TURN", "status": "ERROR", "message": "Bạn chưa tham gia phòng nào"}
            
            # Chuyển lượt chơi
            turn_result = self.game_manager.end_turn(room_id, player_name)
            
            if turn_result.get('success', False):
                next_player = turn_result.get('next_player')
                
                if self.broadcast_callback:
                    await self.broadcast_callback(
                        room_id,
                        f"➡️ {player_name} đã kết thúc lượt. Lượt của **{next_player}**!"
                    )
                
                # Broadcast state update
                await self.broadcast_game_state(room_id)
                
                return {
                    "cmd": "END_TURN", 
                    "status": "OK",
                    "data": turn_result,
                    "message": f"Đã chuyển lượt thành công sang {next_player}"
                }
            else:
                return {
                    "cmd": "END_TURN", 
                    "status": "ERROR", 
                    "message": turn_result.get('message', 'Không thể kết thúc lượt. Có thể chưa đến lượt bạn hoặc bạn chưa tung xúc xắc.')
                }

        except Exception as e:
            self.logger.error(f"❌ Lỗi kết thúc lượt: {e}")
            return {"cmd": "END_TURN", "status": "ERROR", "message": "Lỗi server khi kết thúc lượt"}

    async def handle_chat(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý tin nhắn chat"""
        try:
            room_id = client_info.get('room_id')
            player_name = client_info.get('player_name')
            message = payload.get('message')

            if not room_id or not player_name:
                return {"cmd": "CHAT", "status": "ERROR", "message": "Bạn chưa tham gia phòng nào"}
            
            if not message or not isinstance(message, str):
                return {"cmd": "CHAT", "status": "ERROR", "message": "Tin nhắn không hợp lệ"}

            # Tạo gói tin chat để broadcast
            chat_message = {
                "cmd": "CHAT_MESSAGE",
                "status": "OK",
                "data": {
                    "player_name": player_name,
                    "room_id": room_id,
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Gửi tin nhắn đến tất cả người chơi trong phòng
            await self.send_to_room(room_id, chat_message)
            
            self.logger.info(f"💬 [CHAT - {room_id}] {player_name}: {message}")

            # Gửi phản hồi thành công (không cần phản hồi riêng cho chat)
            return {"cmd": "CHAT", "status": "OK", "message": "Đã gửi tin nhắn"}

        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý chat: {e}")
            return {"cmd": "CHAT", "status": "ERROR", "message": "Lỗi server khi gửi chat"}

    def make_response(cmd: str, status: str = "OK", data: dict = None, message: str = "") -> Dict:
        """Hàm tiện ích để chuẩn hóa response gửi về client"""
        return {"cmd": cmd, "status": status, "data": data, "message": message}


    async def handle_get_player_info(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Lấy thông tin người chơi hiện tại trong phòng"""
        try:
            room_id = client_info.get('room_id')
            player_name = client_info.get('player_name')
            
            if not room_id or not player_name or not player_name.strip():
                return make_response("GET_PLAYER_INFO", "ERROR", None, "Bạn chưa tham gia phòng nào")

            # Lấy thông tin từ game_manager
            player_info = self.game_manager.get_player_info(room_id, player_name)
            if not player_info:
                return make_response("GET_PLAYER_INFO", "ERROR", None, "Không tìm thấy thông tin người chơi")

            return make_response("GET_PLAYER_INFO", "OK", player_info, f"Thông tin người chơi {player_name}")

        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy thông tin người chơi: {e}\n{traceback.format_exc()}")
            return make_response("GET_PLAYER_INFO", "ERROR", None, "Lỗi server khi lấy thông tin người chơi")


    async def handle_get_game_state(self, payload: dict, client_info: dict, connection_type: str) -> Dict:
        """Xử lý lấy toàn bộ trạng thái game (board, players, current_turn)"""
        try:
            room_id = client_info.get('room_id')

            if not room_id:
                return make_response("GET_GAME_STATE", "ERROR", None, "Bạn chưa tham gia phòng nào")

            # Lấy toàn bộ trạng thái game từ Game Manager
            game_state = self.game_manager.get_game_state(room_id)
            
            if not game_state:
                # Nếu game chưa bắt đầu, có thể trả về trạng thái rỗng để client xử lý
                empty_state = {"players": [], "board": {}, "current_turn": None}
                return make_response("GET_GAME_STATE", "OK", empty_state, "Game chưa bắt đầu hoặc chưa có trạng thái")

            return make_response("GAME_STATE", "OK", game_state, "Trạng thái game hiện tại")

        except Exception as e:
            self.logger.error(f"❌ Lỗi lấy trạng thái game: {e}\n{traceback.format_exc()}")
            return make_response("GET_GAME_STATE", "ERROR", None, "Lỗi server khi lấy trạng thái game")
