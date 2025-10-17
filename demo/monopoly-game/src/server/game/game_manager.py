from typing import Dict, Optional, List
import threading
from .game_session import GameSession
from ..utils.logger import Logger
from ..network.multiplecast_manager import MulticastManager

class GameManager:
    """Quản lý nhiều phiên chơi Monopoly (nhiều room)"""

    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger("GameManager")
        self.games: Dict[str, GameSession] = {}
        self.lock = threading.RLock()

    def set_multicast_manager(self, manager: MulticastManager):
        self.multicast_manager = manager
        self.logger.info("✅ MulticastManager đã được gán vào GameManager")


    def get_or_create_game(self, room_id: str, mcast_ip: str = None, mcast_port: int = None) -> GameSession:
        with self.lock:
            if room_id not in self.games:
                self.games[room_id] = GameSession(room_id, self.logger, mcast_ip, mcast_port)
            return self.games[room_id]

    def add_player_to_game(self, room_id: str, player_name: str):
        game = self.get_or_create_game(room_id)
        if player_name not in [p.name for p in game.players.values()]:
            game.add_player(player_name, player_name)

    def is_player_in_game(self, room_id: str, player_name: str) -> bool:
        game = self.games.get(room_id)
        return player_name in [p.name for p in game.players.values()] if game else False
