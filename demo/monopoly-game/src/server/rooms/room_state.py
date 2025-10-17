from datetime import datetime
import copy
from ..game.player import Player
from ..game.board import Board
from typing import List
from ..game.TurnManager import TurnManager


class RoomState:
    """
    Lưu trữ toàn bộ trạng thái phòng:
    - Người chơi
    - Bàn cờ
    - Tiến trình (lượt, winner, thời gian)
    - Hỗ trợ cập nhật động từ GameManager
    """
    # Đây là nơi người chơi tham gia, chờ đợi, và sẵn sàng.
    LOBBY = "lobby"
    min_players = 2

    max_players = 4

    # 2. Trạng thái Đang chơi (In-Game/Running)
    # Trò chơi đã bắt đầu và vòng lặp game đang chạy.
    INGAME = "ingame"

    # 3. Trạng thái Kết thúc (Finished)
    # Trò chơi đã hoàn thành, chờ giải tán phòng.
    FINISHED = "finished"
    def __init__(self, room_id: str, host_id: str, network, logger, players: List['Player'], board: 'Board'):

        self.room_id = room_id
        self.host_id = host_id
        self.network = network  # NetworkManager instance
        self.logger = logger  # Gán logger instance


        # Gán danh sách người chơi và Board đã được tạo bên ngoài
        self.players = players
        self.board = board

        # --- CÁC THUỘC TÍNH ĐỘNG/MẶC ĐỊNH ---
        self.turn_manager = TurnManager(self.players)
        self.status = "lobby"
        self.winner = None

        # --- METADATA/DEBUG ---
        self.start_time = None
        self.end_time = None
        self.snapshots = []

        # Cached previous snapshot
        self._last_snapshot = {}

        self.logger.info(f"[STATE] Room '{self.room_id}' initialized by Host ID: {self.host_id}")

    # ---------------------------------------------------------
    # Core utilities
    # ---------------------------------------------------------
    def add_player(self, player: 'Player'):
        """Thêm người chơi vào phòng và log lại."""
        if self.get_player(player.id):
            self.logger.warning(f"[STATE:{self.room_id}] Player ID {player.id} is already in the room.")
            return

        self.players.append(player)
        self.logger.info(f"[STATE:{self.room_id}] Player '{player.id}' joined. Total players: {len(self.players)}")

    def get_player(self, player_id):
        return next((p for p in self.players if p.id == player_id), None)

    def serialize(self):
        """Trả về bản JSON hóa của RoomState"""
        return {
            "room_id": self.room_id,
            "status": self.status,
            "winner": self.winner,
            "current_turn": self.turn_manager.get_current_player(),
            "start_time": self.start_time.isoformat() if self.start_time else None,  # Xử lý datetime
            "end_time": self.end_time.isoformat() if self.end_time else None,  # Xử lý datetime
            "players": [p.serialize() for p in self.players],
            "board": self.board.serialize_json() if self.board else None,
            "timestamp": datetime.now().isoformat(),
        }

    # ---------------------------------------------------------
    # Cập nhật từ game (tương thích GameManager)
    # ---------------------------------------------------------
    def update_from_game(self, board, players):
        """


        Cập nhật RoomState dựa trên tình hình hiện tại của game.
        Tự động phát hiện thay đổi và gửi sự kiện cập nhật.
        """
        self.board = board
        self.players = players
        self.turn_manager.update_players(players)

        self.logger.debug(f"[STATE:{self.room_id}] Received update from GameManager. Serializing state...")

        new_snapshot = self.serialize()

        # So sánh với snapshot cũ
        diff = self._detect_changes(self._last_snapshot, new_snapshot)

        if diff:
            self.logger.info(f"[STATE:{self.room_id}] State changed detected. Committing snapshot and emitting update.")
            self._commit_snapshot(new_snapshot)
            self._emit_room_update(diff)
        else:
            self.logger.debug(f"[STATE:{self.room_id}] No significant state changes detected. Update skipped.")

    # ---------------------------------------------------------
    # Internal mechanics
    # ---------------------------------------------------------
    def _detect_changes(self, old, new):
        """So sánh hai snapshot → trả về thay đổi"""
        changes = {}

        # Log nếu đây là lần đầu tiên tạo snapshot
        if not old:
            self.logger.debug(f"[STATE:{self.room_id}] First snapshot generated.")
            return new

        # Thêm log chi tiết hơn về quá trình phát hiện
        for key in new.keys():
            if key not in old or old[key] != new[key]:
                # Log chỉ những thay đổi quan trọng (trừ timestamp)
                if key != "timestamp":
                    self.logger.debug(f"[STATE:{self.room_id}] Change found in '{key}'.")
                changes[key] = new[key]

        return changes

    def _commit_snapshot(self, snapshot):
        """Ghi lại snapshot vào lịch sử"""
        self.snapshots.append(copy.deepcopy(snapshot))
        self._last_snapshot = snapshot
        self.logger.debug(f"[STATE:{self.room_id}] Snapshot committed. Total snapshots: {len(self.snapshots)}")

    def _emit_room_update(self, diff):
        """Phát sự kiện cập nhật trạng thái"""
        payload = {
            "type": "ROOM_STATE_UPDATED",
            "room_id": self.room_id,
            "diff": diff,
            "timestamp": datetime.now().isoformat(),
        }
        self.network.emit_event("ROOM_STATE_UPDATED", payload)
        self.logger.info(f"[STATE:{self.room_id}] Emitted update event with {len(diff)} changes.")