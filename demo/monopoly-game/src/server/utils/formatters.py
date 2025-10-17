"""Format output đẹp cho server"""
import time
from datetime import datetime
from typing import Dict, List

class ServerFormatter:
    """Format các thông báo server"""
    
    @staticmethod
    def format_server_status(rooms_count: int, players_count: int, clients_count: int) -> str:
        """Format trạng thái server"""
        return f"📊 SERVER STATUS | Phòng: {rooms_count} | Người chơi: {players_count} | Client: {clients_count}"
    
    @staticmethod
    def format_room_list(rooms_data: Dict) -> str:
        """Format danh sách phòng"""
        if not rooms_data:
            return "📭 Không có phòng nào đang hoạt động"
        
        output = ["📋 DANH SÁCH PHÒNG ĐANG HOẠT ĐỘNG", "=" * 60]
        
        for room_id, room_info in rooms_data.items():
            players = room_info.get('players', [])
            room_name = room_info.get('room_name', room_id)
            max_players = room_info.get('max_players', 4)
            
            output.extend([
                f"🏠 {room_name}",
                f"   🆔 {room_id}",
                f"   👥 {len(players)}/{max_players} người chơi",
                f"   🎮 {', '.join(players) if players else 'Đang chờ...'}",
                f"   🌐 {room_info.get('multicast_ip', 'N/A')}:{room_info.get('port', 'N/A')}",
                "-" * 40
            ])
        
        return "\n".join(output)
    
    @staticmethod
    def format_player_join(player_name: str, room_name: str, current_players: int, max_players: int) -> str:
        """Format thông báo người chơi tham gia"""
        return f"🎊 {player_name} đã tham gia {room_name}!\n   👥 Hiện tại: {current_players}/{max_players} người"
    
    @staticmethod
    def format_room_created(room_name: str, host_name: str, max_players: int) -> str:
        """Format thông báo tạo phòng"""
        return f"🏠 Phòng '{room_name}' đã được tạo bởi {host_name} (Tối đa: {max_players} người)"
    
    @staticmethod
    def format_system_message(message: str) -> str:
        """Format tin nhắn hệ thống"""
        return f"📢 [HỆ THỐNG] {message}"
    
    @staticmethod
    def format_error(error_type: str, details: str) -> str:
        """Format thông báo lỗi"""
        return f"❌ {error_type.upper()}: {details}"