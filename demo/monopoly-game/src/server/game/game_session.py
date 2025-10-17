# game/game_session.py
import threading
import random
from typing import Dict, Optional, List

from .board import Board
from .player import Player
from ..utils.logger import Logger
from ..utils.network_utils import create_udp_socket, udp_send
from ..utils.packet_format import PacketFormat
import json
from pathlib import Path


with open(Path(__file__).parent / "community_chest.json", "r", encoding="utf-8") as f:
    community_chest_cards = [c["text"] for c in json.load(f)]

with open(Path(__file__).parent / "chance.json", "r", encoding="utf-8") as f:
    chance_cards = [c["text"] for c in json.load(f)]

class GameSession:
    """
    Quản lý 1 phiên chơi Monopoly cụ thể (1 room)
    """

    def __init__(self, room_id: str, logger: Optional[Logger] = None,
                 mcast_ip: str = None, mcast_port: int = None):
        self.room_id = room_id
        self.board = Board()
        self.players: Dict[str, Player] = {}
        self.turn_order: List[str] = []
        self.current_turn_index = 0
        self.round_number = 1
        self.active = False
        self.winner: Optional[str] = None

        self.community_chest_cards = COMMUNITY_CHEST_CARDS.copy()
        self.chance_cards = CHANCE_CARDS.copy()
        
        self.seq_counter = 0
        self.lock = threading.RLock()
        self.logger = logger or Logger(f"GameSession-{room_id}")

        self.mcast_ip = mcast_ip
        self.mcast_port = mcast_port
        self.multicast_manager = None

        self.logger.info(f"[GameSession] Created for {room_id} with multicast: {mcast_ip}:{mcast_port}")

    # ==========================
    # Player & Turn Management
    # ==========================
    def add_player(self, player_id: str, name: str) -> bool:
        with self.lock:
            if player_id in self.players:
                return False
            p = Player(player_id, name)
            self.players[player_id] = p
            self.turn_order.append(player_id)
            return True

    def remove_player(self, player_id: str) -> bool:
        with self.lock:
            if player_id not in self.players:
                return False
            if player_id in self.turn_order:
                idx = self.turn_order.index(player_id)
                del self.turn_order[idx]
                if idx <= self.current_turn_index and self.current_turn_index > 0:
                    self.current_turn_index -= 1
            del self.players[player_id]
            self._check_end_conditions()
            return True

    def get_current_player_id(self) -> Optional[str]:
        if not self.turn_order:
            return None
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
        return self.turn_order[self.current_turn_index]

    def get_current_player(self) -> Optional[Player]:
        pid = self.get_current_player_id()
        return self.players.get(pid) if pid else None

    # ==========================
    # Game Lifecycle
    # ==========================
    def start_game(self) -> bool:
        if len(self.players) < 2:
            return False
        self.active = True
        self.current_turn_index = 0
        self.round_number = 1
        self.winner = None
        return True

    def end_game(self):
        self.active = False

    def _check_end_conditions(self):
        alive = [p for p in self.players.values() if not p.is_bankrupt()]
        if len(alive) == 1:
            self.winner = alive[0].id
            self.active = False

    def _advance_turn(self):
        if not self.turn_order:
            return
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        if self.current_turn_index == 0:
            self.round_number += 1

    # ==========================
    # Dice & Actions
    # ==========================
    def roll(self, player_id: str) -> dict:
        if not self.active or self.get_current_player_id() != player_id:
            return {"status": "ERROR", "message": "Not your turn or game inactive"}
        player = self.players[player_id]
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        total = d1 + d2
        old_pos = player.position
        new_pos = player.move(total, board_size=len(self.board.tiles))
        self._advance_turn()
        return {"player": player_id, "dice": [d1, d2], "total": total,
                "old_pos": old_pos, "new_pos": new_pos}

    def buy(self, player_id: str) -> dict:
        player = self.players.get(player_id)
        if not player:
            return {"status": "ERROR", "message": "Player not found"}

        tile = self.board.get_tile(player.position)
        if not tile:
            return {"status": "ERROR", "message": "Tile not found"}
        if tile.get("owner") is not None:
            return {"status": "ERROR", "message": "Tile already owned"}

        # Giả sử giá tile được lưu trong tile['price']
        price = tile.get("price", 0)
        if player.money < price:
            return {"status": "ERROR", "message": "Not enough money"}

        # Mua thành công
        player.money -= price
        tile["owner"] = player_id
        return {"status": "OK", "player": player_id, "tile": player.position, "money_left": player.money}

