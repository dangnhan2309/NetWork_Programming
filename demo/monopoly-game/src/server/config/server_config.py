"""Cấu hình server"""
import os
from typing import Dict

class ServerConfig:
    """Quản lý cấu hình server"""
    
    def __init__(self):
        self.tcp_host = os.getenv('TCP_HOST', '0.0.0.0')
        self.tcp_port = int(os.getenv('TCP_PORT', '5050'))
        self.udp_ttl = 2
        self.tick_rate = 5.0
        self.max_players_per_room = 6
        self.min_players_to_start = 2
        
    def to_dict(self) -> Dict:
        """Chuyển cấu hình thành dictionary"""
        return {
            "tcp_host": self.tcp_host,
            "tcp_port": self.tcp_port,
            "udp_ttl": self.udp_ttl,
            "tick_rate": self.tick_rate,
            "max_players_per_room": self.max_players_per_room,
            "min_players_to_start": self.min_players_to_start
        }

# Instance to be imported
SERVER_CONFIG = ServerConfig()