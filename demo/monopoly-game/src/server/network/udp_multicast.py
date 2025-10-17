# src/server/network/udp_handler.py
"""Xử lý UDP Multicast cho các phòng game"""
import asyncio
import socket
import struct
import json
from typing import Dict, List, Optional
from ..utils.logger import Logger
from ..utils.formatters import ServerFormatter
from ..utils.packet_format import PacketFormat
from ..utils.network_utils import create_udp_socket, join_multicast_group, leave_multicast_group, udp_send, udp_receive
from ..rooms.room_manager import RoomManager
from .multiplecast_manager import MulticastManager
from ..utils.network_utils import safe_udp_receive

class UDPHandler:
    """Xử lý UDP Multicast cho các phòng game"""
    def __init__(self, room_manager: RoomManager, logger: Logger, multicast_manager: MulticastManager):
        self.room_manager = room_manager
        self.logger = logger
        self.formatter = ServerFormatter()
        self.multicast_manager = multicast_manager
        self.running_event = asyncio.Event()
        self._tasks: Dict[str, asyncio.Task] = {}
        self.heartbeat_interval = 30

    async def run(self):
        """Chạy UDP handler - khởi động tất cả phòng hiện tại"""
        self.logger.info(self.formatter.format_system_message("UDP Handler đã khởi động"))
        self.running_event.set()  # bật trạng thái chạy
        
        try:
            while self.running_event.is_set():
                # Tạo task cho các phòng chưa có task
                for room_id in list(self.multicast_manager.groups.keys()):
                    if room_id not in self._tasks:
                        self._tasks[room_id] = asyncio.create_task(self._process_room(room_id))
                
                # Xóa task của các phòng đã đóng
                closed_rooms = [rid for rid in self._tasks if rid not in self.multicast_manager.groups]
                for rid in closed_rooms:
                    task = self._tasks.pop(rid)
                    task.cancel()
                
                # Gửi heartbeat định kỳ
                await self.send_heartbeats()
                await asyncio.sleep(0.1)  # tránh high CPU
        except Exception as e:
            self.logger.error(self.formatter.format_error("UDP Handler", str(e)))
        finally:
            await self.cleanup()

    async def _process_room(self, room_id: str):
        """Xử lý UDP messages cho từng phòng riêng"""
        try:
            while self.running_event.is_set() and self.multicast_manager.is_room_active(room_id):
                try:
                    sock = self.multicast_manager.get_group(room_id)["socket"]
                    packet, addr = safe_udp_receive(sock)
                    if packet and addr:
                        await self.handle_udp_packet(room_id, packet, addr)
                except Exception as e:
                    self.logger.error(f"❌ Lỗi xử lý UDP phòng {room_id}: {e}")
                
                await asyncio.sleep(0)  # yield control
        except asyncio.CancelledError:
            self.logger.info(f"🛑 Task UDP phòng {room_id} bị hủy")
        except Exception as e:
            self.logger.error(f"❌ Lỗi task UDP phòng {room_id}: {e}")

    def stop(self):
        """Dừng UDP Handler"""
        self.running_event.clear()
        for task in self._tasks.values():
            task.cancel()
        
    async def handle_udp_packet(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý packet UDP - CHỈ XỬ LÝ PACKET TỪ CLIENT"""
        try:
            sender = packet.get("header", {}).get("sender", "unknown")
            
            # CHỈ XỬ LÝ PACKET TỪ CLIENT, KHÔNG PHẢI SERVER
            if sender == "server":
                return  # Bỏ qua hoàn toàn
                
            packet_type = packet.get("header", {}).get("type", "unknown")
            action = packet.get("command", {}).get("action", "unknown")
            
            self.logger.debug(f"📨 UDP từ client {sender} trong {room_id}: {packet_type}/{action}")
            
            # ... phần xử lý còn lại giữ nguyên
            handlers = {
                "game_action": self.handle_game_action,
                "chat_message": self.handle_chat_message,
                "heartbeat": self.handle_heartbeat,
                "system_message": self.handle_system_message,
                "player_move": self.handle_player_move,
                "property_purchase": self.handle_property_purchase
            }
            
            handler = handlers.get(packet_type)
            if handler:
                await handler(room_id, packet, addr)
            else:
                self.logger.warning(f"⚠️ UDP packet type không xác định: {packet_type}")
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý UDP packet: {e}")
    
    async def handle_game_action(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý action game qua UDP"""
        try:
            action = packet.get("command", {}).get("action")
            player_name = packet.get("header", {}).get("sender")
            args = packet.get("command", {}).get("args", {})
            
            self.logger.info(f"🎮 UDP Game action từ {player_name}: {action}")
            
            # Broadcast action đến tất cả players trong phòng
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý game action: {e}")
    
    async def handle_chat_message(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý tin nhắn chat qua UDP"""
        try:
            message = packet.get("payload", {}).get("message", "")
            player_name = packet.get("header", {}).get("sender", "Unknown")
            
            self.logger.info(f"💬 UDP Chat từ {player_name} trong {room_id}: {message}")
            
            # Broadcast tin nhắn đến tất cả players trong phòng
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý chat message: {e}")
    
    async def handle_heartbeat(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý heartbeat từ client"""
        try:
            player_name = packet.get("header", {}).get("sender")
            self.logger.debug(f"💓 UDP Heartbeat từ {player_name} trong {room_id}")
            
            # Gửi heartbeat response
            response_packet = PacketFormat.create_packet(
                packet_type="heartbeat",
                room_id=room_id,
                sender="server",
                target=player_name,
                action="heartbeat_response",
                payload={"status": "alive", "timestamp": PacketFormat.generate_timestamp()}
            )
            
            await self.send_to_room(room_id, response_packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý heartbeat: {e}")
    
    async def handle_system_message(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý system message"""
        try:
            message = packet.get("payload", {}).get("message", "")
            self.logger.info(f"📢 UDP System message trong {room_id}: {message}")
            
            # Broadcast system message
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý system message: {e}")

    async def handle_player_move(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý di chuyển người chơi"""
        try:
            player_name = packet.get("header", {}).get("sender")
            new_position = packet.get("payload", {}).get("position", 0)
            
            self.logger.info(f"👣 {player_name} di chuyển đến ô {new_position} trong {room_id}")
            
            # Broadcast thông tin di chuyển
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý player move: {e}")

    async def handle_property_purchase(self, room_id: str, packet: dict, addr: tuple):
        """Xử lý mua tài sản"""
        try:
            player_name = packet.get("header", {}).get("sender")
            property_id = packet.get("payload", {}).get("property_id")
            
            self.logger.info(f"🏠 {player_name} mua tài sản {property_id} trong {room_id}")
            
            # Broadcast thông tin mua tài sản
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi xử lý property purchase: {e}")
    
    async def setup_room_multicast(self, room_id: str, multicast_ip: str, port: int) -> bool:
        """Thiết lập multicast socket cho phòng - THÊM LOG CHI TIẾT"""
        try:
            self.logger.info(f"🔧 Setting up multicast for {room_id} at {multicast_ip}:{port}")
            
            if room_id in self.multicast_manager.groups:
                self.logger.info(f"🔄 Multicast socket cho {room_id} đã tồn tại")
                return True
            
            group_info = self.multicast_manager.create_group(room_id, multicast_ip, port)
            
            if group_info:
                self.logger.info(self.formatter.format_system_message(
                    f"✅ Đã thiết lập multicast cho {room_id} tại {multicast_ip}:{port}"
                ))
                return True
            else:
                self.logger.error(f"❌ Failed to create multicast group for {room_id}")
                return False
                
        except Exception as e:
            self.logger.error(self.formatter.format_error("Thiết lập multicast", str(e)))
            return False
    
    async def broadcast_system_message(self, room_id: str, message: str):
        """Broadcast system message đến phòng"""
        try:
            if not self.multicast_manager.is_room_active(room_id):
                self.logger.warning(f"⚠️ Không tìm thấy multicast socket cho {room_id}")
                return
            
            success = self.multicast_manager.broadcast_system_message(room_id, message)
            
            if success:
                self.logger.info(f"📢 Đã broadcast system message đến {room_id}: {message}")
            else:
                self.logger.error(f"❌ Lỗi broadcast system message đến {room_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi broadcast system message: {e}")
    
    async def broadcast_to_room(self, room_id: str, packet: dict):
        """Broadcast packet đến tất cả clients trong phòng"""
        try:
            if not self.multicast_manager.is_room_active(room_id):
                self.logger.warning(f"⚠️ Không thể broadcast - không tìm thấy socket cho {room_id}")
                return
            
            success = self.multicast_manager.broadcast_to_room(room_id, packet)
            
            if not success:
                self.logger.error(f"❌ Lỗi broadcast packet đến {room_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi broadcast đến {room_id}: {e}")
    
    async def send_to_room(self, room_id: str, packet: dict):
        """Gửi packet đến phòng (alias cho broadcast)"""
        await self.broadcast_to_room(room_id, packet)

    async def auto_setup_room_multicast(self, room_id: str):
        """Tự động thiết lập multicast khi phòng được tạo"""
        try:
            room_info = self.room_manager.get_room_info(room_id)
            if not room_info:
                self.logger.warning(f"⚠️ Room {room_id} not found for auto-setup")
                return False
                
            multicast_ip = room_info.get('multicast_ip')
            port = room_info.get('port')
            
            if not multicast_ip or not port:
                self.logger.error(f"❌ No multicast info for {room_id}")
                return False
                
            # KIỂM TRA VÀ TẠO MULTICAST SOCKET NẾU CHƯA CÓ
            if not self.multicast_manager.is_room_active(room_id):
                self.logger.info(f"🔧 Auto-setting up multicast for {room_id} at {multicast_ip}:{port}")
                success = await self.setup_room_multicast(room_id, multicast_ip, port)
                
                if success:
                    self.logger.info(f"✅ Auto-setup multicast successful for {room_id}")
                    return True
                else:
                    self.logger.error(f"❌ Auto-setup multicast failed for {room_id}")
                    return False
            else:
                self.logger.info(f"✅ Multicast already active for {room_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error in auto_setup_room_multicast: {e}")
            return False
    async def send_heartbeats(self):
        """Gửi heartbeat đến các phòng đang active - GIẢM TẦN SUẤT"""
        try:
            # CHỈ GỬI HEARTBEAT MỖI 30 GIÂY, KHÔNG PHẢI MỖI LẦN LẶP
            current_time = asyncio.get_event_loop().time()
            if hasattr(self, '_last_heartbeat') and current_time - self._last_heartbeat < 30:
                return
                
            self._last_heartbeat = current_time
            
            for room_id in list(self.multicast_manager.groups.keys()):
                room_info = self.room_manager.get_room_info(room_id)
                if room_info and room_info.get('game_started', False):
                    success = self.multicast_manager.send_heartbeat(room_id)
                    
                    if success:
                        self.logger.debug(f"💓 Đã gửi heartbeat đến {room_id}")
                    else:
                        self.logger.error(f"❌ Lỗi gửi heartbeat đến {room_id}")
                        
        except Exception as e:
            self.logger.error(f"❌ Lỗi gửi heartbeat: {e}")
    
    async def remove_room_multicast(self, room_id: str):
        """Dọn dẹp multicast socket khi phòng đóng"""
        try:
            self.multicast_manager.remove_group(room_id)
            self.logger.info(self.formatter.format_system_message(f"Đã đóng multicast cho {room_id}"))
                
        except Exception as e:
            self.logger.error(f"❌ Lỗi đóng multicast cho {room_id}: {e}")
    
    async def cleanup(self):
        """Dọn dẹp tất cả multicast sockets"""
        self.logger.info(self.formatter.format_system_message("Đang dọn dẹp UDP Handler..."))
        
        self.multicast_manager.cleanup_all_groups()
        
        self.logger.info(self.formatter.format_system_message("UDP Handler đã dọn dẹp xong"))
    
    def get_multicast_info(self, room_id: str) -> Optional[Dict]:
        """Lấy thông tin multicast của phòng"""
        room_info = self.room_manager.get_room_info(room_id)
        if room_info:
            return {
                "multicast_ip": room_info.get('multicast_ip'),
                "port": room_info.get('port'),
                "has_socket": self.multicast_manager.is_room_active(room_id)
            }
        return None
    
    def get_active_rooms_count(self) -> int:
        """Lấy số lượng phòng đang có multicast active"""
        return self.multicast_manager.get_active_rooms_count()

    async def broadcast_game_state(self, room_id: str, game_state: dict):
        """Broadcast trạng thái game đến phòng"""
        try:
            packet = PacketFormat.create_packet(
                packet_type="game_state",
                room_id=room_id,
                sender="server",
                target="all",
                action="state_update",
                payload=game_state
            )
            
            await self.broadcast_to_room(room_id, packet)
            self.logger.info(f"🎮 Đã broadcast game state đến {room_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi broadcast game state: {e}")

    async def broadcast_player_joined(self, room_id: str, player_name: str):
        """Broadcast thông báo người chơi tham gia"""
        try:
            packet = PacketFormat.create_packet(
                packet_type="player_joined",
                room_id=room_id,
                sender="server",
                target="all",
                action="player_joined",
                payload={
                    "player_name": player_name,
                    "timestamp": PacketFormat.generate_timestamp(),
                    "message": f"{player_name} đã tham gia phòng"
                }
            )
            
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi broadcast player joined: {e}")

    async def broadcast_player_left(self, room_id: str, player_name: str):
        """Broadcast thông báo người chơi rời đi"""
        try:
            packet = PacketFormat.create_packet(
                packet_type="player_left",
                room_id=room_id,
                sender="server",
                target="all",
                action="player_left",
                payload={
                    "player_name": player_name,
                    "timestamp": PacketFormat.generate_timestamp(),
                    "message": f"{player_name} đã rời phòng"
                }
            )
            
            await self.broadcast_to_room(room_id, packet)
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi broadcast player left: {e}")