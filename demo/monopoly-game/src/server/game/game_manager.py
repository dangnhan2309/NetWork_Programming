# game/game_manager.py

"""
GameManager – Monopoly Server
------------------------------
Quản lý logic game Monopoly trong 1 phòng:
- Board, Players, Turns, Round
- Gửi trực tiếp các sự kiện game qua UDP multicast
- Không còn phụ thuộc UDPMulticast / MulticastManager
"""

import threading
import random
from typing import Dict, Optional, List

from .board import Board
from .player import Player
from ..utils import packetformat as PacketFormat
from ..utils import logger as Logger
from ..network import network_utils as net

community_chest_cards = [
    "Advance to Go (Collect $200)",
    "Bank error in your favor – Collect $200",
    "Doctor’s fees – Pay $50",
    "From sale of stock you get $50",
    "Get Out of Jail Free",
    "Go to Jail – Go directly to jail – Do not pass Go – Do not collect $200",
    "Grand Opera Night – Collect $50 from every player for opening night seats",
    "Holiday Fund matures – Receive $100",
    "Income tax refund – Collect $20",
    "It is your birthday – Collect $10 from every player",
    "Life insurance matures – Collect $100",
    "Hospital Fees – Pay $50",
    "School fees – Pay $50",
    "Receive $25 consultancy fee",
    "You are assessed for street repairs – $40 per house, $115 per hotel",
    "You have won second prize in a beauty contest – Collect $10"
]

chance_cards = [
    "Advance to Go (Collect $200)",
    "Advance to Illinois Ave. If you pass Go, collect $200",
    "Advance to St. Charles Place. If you pass Go, collect $200",
    "Advance token to nearest Utility. If unowned, buy it. If owned, pay rent.",
    "Advance token to nearest Railroad. Pay owner double rent. If unowned, you may buy.",
    "Bank pays you dividend of $50",
    "Get Out of Jail Free",
    "Go Back 3 Spaces",
    "Go to Jail – Go directly to jail – Do not pass Go – Do not collect $200",
    "Make general repairs on all your property: For each house pay $25, For each hotel $100",
    "Pay poor tax of $15",
    "Take a trip to Reading Railroad. If you pass Go, collect $200",
    "Take a walk on the Boardwalk. Advance token to Boardwalk",
    "You have been elected Chairman of the Board – Pay each player $50",
    "Your building loan matures – Collect $150",
    "You have won a crossword competition – Collect $100"
]

class GameManager:
    """
    Quản lý 1 phiên chơi Monopoly (1 room)
    """

    def __init__(self, room_id: str, logger: Optional[Logger] = None,
                 mcast_ip: str = None, mcast_port: int = None):
        self.room_id = room_id
        self.board = Board()
        self.players: Dict[str, Player] = {}
        self.turn_order: List[str] = []
        self.current_turn_index: int = 0
        self.round_number: int = 1
        self.active: bool = False
        self.winner: Optional[str] = None

        self.seq_counter = 0
        self.lock = threading.RLock()
        self.logger = logger or Logger(room_id)

        # Multicast target cho tất cả sự kiện/state
        self.mcast_ip = mcast_ip
        self.mcast_port = mcast_port

    # -------------------------
    # Packet helpers
    # -------------------------
    def _next_seq(self) -> int:
        with self.lock:
            self.seq_counter += 1
            return self.seq_counter

    def build_state_packet(self) -> dict:
        with self.lock:
            players_state = {pid: p.to_dict() for pid, p in self.players.items()}
            data = {
                "room_id": self.room_id,
                "round": self.round_number,
                "current_turn": self.get_current_player_id(),
                "players": players_state,
                "winner": self.winner,
                "active": self.active
            }
            return PacketFormat.create_packet(
                packet_type="STATE",
                room_id=self.room_id,
                sender="SERVER",
                target="ALL",
                action="STATE_UPDATE",
                args={},
                payload={"data": data, "status": "OK"},
                seq_id=self._next_seq(),
                ack=False,
                reliable=True,
                hop_count=1
            )

    def build_event_packet(self, action: str, payload: dict, target: str = "ALL") -> dict:
        return PacketFormat.create_packet(
            packet_type="EVENT",
            room_id=self.room_id,
            sender="SERVER",
            target=target,
            action=action,
            args={},
            payload=payload,
            seq_id=self._next_seq(),
            ack=False,
            reliable=False,
            hop_count=1
        )

    # -------------------------
    # Network send helpers
    # -------------------------
    def send_state_update(self):
        if self.mcast_ip and self.mcast_port:
            packet = self.build_state_packet()
            sock = net.create_udp_socket(multicast=True)
            net.send_udp(sock, packet, (self.mcast_ip, self.mcast_port))
            sock.close()
            self.logger.debug(f"[GameManager] STATE_UPDATE sent to {self.mcast_ip}:{self.mcast_port}")

    def send_event(self, action: str, payload: dict, target: str = "ALL"):
        if self.mcast_ip and self.mcast_port:
            packet = self.build_event_packet(action, payload, target)
            sock = net.create_udp_socket(multicast=True)
            net.send_udp(sock, packet, (self.mcast_ip, self.mcast_port))
            sock.close()
            self.logger.debug(f"[GameManager] EVENT {action} sent to {self.mcast_ip}:{self.mcast_port}")

    # -------------------------
    # Player management
    # -------------------------
    def add_player(self, player_id: str, name: str) -> bool:
        with self.lock:
            if player_id in self.players:
                self.logger.warning(f"[GameManager] Player {player_id} already exists")
                return False
            p = Player(player_id=player_id, name=name)
            self.players[player_id] = p
            self.turn_order.append(player_id)
            self.logger.info(f"[GameManager] Player added: {player_id}")
            self.send_state_update()
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
            self.logger.info(f"[GameManager] Player removed: {player_id}")
            self._check_end_conditions()
            self.send_state_update()
            return True

    def get_current_player_id(self) -> Optional[str]:
        with self.lock:
            if not self.turn_order:
                return None
            if self.current_turn_index >= len(self.turn_order):
                self.current_turn_index = 0
            return self.turn_order[self.current_turn_index]

    def get_current_player(self) -> Optional[Player]:
        pid = self.get_current_player_id()
        return self.players.get(pid) if pid else None

    # -------------------------
    # Game lifecycle
    # -------------------------
    def start_game(self) -> bool:
        with self.lock:
            if len(self.players) < 2:
                self.logger.warning("[GameManager] Need at least 2 players to start")
                return False
            self.active = True
            self.current_turn_index = 0
            self.round_number = 1
            self.winner = None
            self.logger.info(f"[GameManager] Game started")
            self.send_event("GAME_STARTED", {"status": "OK"})
            self.send_state_update()
            return True

    def end_game(self):
        with self.lock:
            self.active = False
            self.logger.info(f"[GameManager] Game ended. Winner: {self.winner}")
            self.send_event("GAME_ENDED", {"winner": self.winner})
            self.send_state_update()

    def _check_end_conditions(self):
        alive = [p for p in self.players.values() if not p.is_bankrupt()]
        if len(alive) == 1:
            self.winner = alive[0].id
            self.active = False
            self.logger.info(f"[GameManager] Winner determined: {self.winner}")
            self.send_event("GAME_ENDED", {"winner": self.winner})
            self.send_state_update()

    # -------------------------
    # Core actions
    # -------------------------
    def roll(self, player_id: str) -> dict:
        with self.lock:
            if not self.active:
                return {"status": "ERROR", "message": "Game not active"}
            if self.get_current_player_id() != player_id:
                return {"status": "ERROR", "message": "Not your turn"}

            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            total = d1 + d2

            player = self.players[player_id]
            old_pos = player.position
            new_pos = player.move(total, board_size=len(self.board.tiles))
            tile = self.board.get_tile(new_pos)

            rent_paid = 0
            events = []

            if tile and tile.get("type") in ("property", "railroad", "utility"):
                owner = tile.get("owner")
                if owner and owner != player_id:
                    rent = self.board.get_rent(new_pos, dice_roll=total) if tile["type"] == "utility" else self.board.get_rent(new_pos)
                    rent_paid = rent if player.pay(rent, receiver=self.players.get(owner)) else 0
                    events.append(f"Paid rent {rent} to {owner}" if rent_paid else "Bankrupt paying rent")

            if tile and tile.get("type") == "go_to_jail":
                player.send_to_jail(10)
                events.append("Sent to Jail")
            if tile and tile.get("type") in ("community_chest", "chance"):
                card = self.draw_card(tile["type"])
                events += self.handler_card_content(player_id, card)
            self._advance_turn()

            payload = {
                "player": player_id,
                "dice": [d1, d2],
                "total": total,
                "old_pos": old_pos,
                "new_pos": new_pos,
                "tile": tile,
                "rent_paid": rent_paid,
                "events": events,
                "status": "OK"
            }

            self.logger.info(f"[GameManager] ROLL {player_id}: {d1}+{d2} -> {new_pos}")
            self.send_event("ROLL_RESULT", payload)
            self.send_state_update()
            return payload

    def buy(self, player_id: str) -> dict:
        with self.lock:
            player = self.players.get(player_id)
            if not player:
                return {"status": "ERROR", "message": "Player not found"}
            tile = self.board.get_tile(player.position)
            if not tile or not self.board.is_property(tile):
                return {"status": "ERROR", "message": "No purchasable property here"}
            if tile.get("owner") is not None:
                return {"status": "ERROR", "message": "Property already owned"}

            price = tile.get("price", 0)
            if player.money < price:
                return {"status": "ERROR", "message": "Insufficient funds"}

            success = self.board.buy_property(tile_id=player.position, player_id=player_id)
            if success:
                player.pay(price)
                player.add_property(player.position)
                payload = {"status": "OK", "tile_id": player.position, "message": "Property purchased"}
                self.send_event("PROPERTY_BOUGHT", payload)
                self.send_state_update()
                return payload
            return {"status": "ERROR", "message": "Buy failed"}

    def pay(self, from_id: str, to_id: str, amount: int) -> dict:
        with self.lock:
            payer = self.players.get(from_id)
            receiver = self.players.get(to_id)
            if not payer or not receiver or amount <= 0:
                return {"status": "ERROR", "message": "Invalid payment"}
            success = payer.pay(amount, receiver=receiver)
            payload = {"from": from_id, "to": to_id, "amount": amount, "status": "OK" if success else "ERROR"}
            self.send_event("PAYMENT", payload)
            self.send_state_update()
            if not success:
                self._handle_bankruptcy(payer)
            return payload

    def end_turn(self, player_id: str) -> dict:
        with self.lock:
            if self.get_current_player_id() != player_id:
                return {"status": "ERROR", "message": "Not your turn"}
            self._advance_turn()
            payload = {"player": player_id, "status": "OK"}
            self.send_event("TURN_ENDED", payload)
            self.send_state_update()
            return payload

    # -------------------------
    # Internal helpers
    # -------------------------
    def _advance_turn(self):
        if not self.turn_order:
            return
        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        if self.current_turn_index == 0:
            self.round_number += 1

    def _handle_bankruptcy(self, player: Player):
        player.bankrupt = True
        self.board.reset_owner(player.id)
        if player.id in self.turn_order:
            self.turn_order.remove(player.id)
        self.logger.info(f"[GameManager] Player bankrupt: {player.id}")
        self._check_end_conditions()
        self.send_event("BANKRUPTCY", {"player": player.id})
        self.send_state_update()

    # -------------------------
    # Command dispatcher
    # -------------------------
    def handle_command(self, packet: dict) -> dict:
        """
        Xử lý packet command từ client.
        Caller không cần gửi event/state, GameManager tự lo.
        """
        try:
            if not PacketFormat.is_valid(packet):
                return {"status": "ERROR", "message": "Invalid packet format"}

            action = packet["command"]["action"].upper()
            sender = packet["header"]["sender"]
            args = packet["command"].get("args", {}) or {}

            if action == "JOIN":
                return {"status": "OK" if self.add_player(sender, sender) else "ERROR"}
            if action == "LEAVE":
                return {"status": "OK" if self.remove_player(sender) else "ERROR"}
            if action == "START_GAME":
                return {"status": "OK" if self.start_game() else "ERROR"}
            if action == "ROLL":
                return self.roll(sender)
            if action == "BUY":
                return self.buy(sender)
            if action == "PAY":
                return self.pay(sender, args.get("to"), int(args.get("amount", 0)))
            if action == "END_TURN":
                return self.end_turn(sender)
            if action == "STATE_REQUEST":
                return {"status": "OK", "state": self.build_state_packet()["payload"]["data"]}
            return {"status": "ERROR", "message": f"Unknown action {action}"}
        except Exception as e:
            self.logger.error(f"[GameManager] handle_command error: {e}")
            return {"status": "ERROR", "message": "Internal server error"}



    # -------------------------
    # Draw / Handle Card
    # -------------------------
    def draw_card(self, deck_type: str) -> str:
        """Chọn ngẫu nhiên 1 lá bài từ deck"""
        deck = self.community_chest_cards if deck_type == "community_chest" else self.chance_cards
        return random.choice(deck)

    def handler_card_content(self, player_id: str, card: str):
        """
        Xử lý nội dung của lá bài:
        - Cập nhật tiền, vị trí, đi tù, trả tiền cho người chơi khác...
        - Gửi event DRAW_CARD cho tất cả người chơi
        """
        player = self.players.get(player_id)
        if not player:
            return

        events = []

        # Simple string-based rules
        if "Collect $" in card:
            amount = int(''.join(filter(str.isdigit, card)))
            player.money += amount
            events.append(f"Received ${amount}")

        if "Pay $" in card:
            amount = int(''.join(filter(str.isdigit, card)))
            if not player.pay(amount):
                self._handle_bankruptcy(player)
            events.append(f"Paid ${amount}")

        if "Go to Jail" in card:
            player.send_to_jail(10)
            events.append("Sent to Jail")

        if "Advance to Go" in card:
            player.position = 0
            player.money += 200
            events.append("Advanced to Go and collected $200")

        if "Go Back 3 Spaces" in card:
            player.position = max(0, player.position - 3)
            events.append("Moved back 3 spaces")

        # Có thể thêm xử lý nâng cao hơn dựa theo tên property, utility, etc.

        # Gửi DRAW_CARD event multicast
        payload = {
            "player": player_id,
            "card": card,
            "events": events
        }
        self.send_event("DRAW_CARD", payload)

        return events
