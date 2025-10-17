# game/core/card_manager.py
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player
    from .board import Board


# ======================================================
# ⚙️ CẤU HÌNH ĐƯỜNG DẪN FILE
# ======================================================
CHANCE_CARD_PATH = Path("chance_cards.json")
COMMUNITY_CHEST_PATH = Path("community_chest.json")


class CardManager:
    """
    Quản lý logic rút và xử lý thẻ (Chance / Community Chest).
    - CHỈ TẠO RA DICTIONARY (instruction).
    - KHÔNG trực tiếp thay đổi Player, Bank, hay Board.
    """

    def __init__(self):
        self.decks = {
            "chance": self._load_deck(CHANCE_CARD_PATH),
            "community": self._load_deck(COMMUNITY_CHEST_PATH)
        }
        # Cờ quản lý việc tồn tại của thẻ "Get out of Jail Free"
        self.jail_card_in_chance = True
        self.jail_card_in_community = True

    # ======================================================
    # 1️⃣ LOAD DỮ LIỆU THẺ
    # ======================================================
    def _load_deck(self, filepath: Path) -> List[Dict[str, Any]]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[CardManager] ⚠️ File not found: {filepath}")
            return []

        cards = []
        for card in data.get("cards", []):
            card["effect_fn"] = self._map_effect(card["action"])
            cards.append(card)
        return cards

    # ======================================================
    # 2️⃣ MAP ACTION → HANDLER FUNCTION
    # ======================================================
    def _map_effect(self, action: str):
        mapping = {
            "move_to": self._handle_move_to,
            "move_back": self._handle_move_back,
            "nearest_utility": self._handle_nearest_utility,
            "nearest_railroad": self._handle_nearest_railroad,
            "go_to_jail": self._handle_go_to_jail,
            "earn": self._handle_earn,
            "pay": self._handle_pay,
            "pay_others": self._handle_pay_others,
            "collect_from_others": self._handle_collect_from_others,
            "property_repair": self._handle_property_repair,
            "get_out_of_jail_card": self._handle_get_out_of_jail_card,
        }
        return mapping.get(action, self._handle_default)

    # ======================================================
    # 3️⃣ RÚT NGẪU NHIÊN 1 THẺ
    # ======================================================
    def draw_card(self, deck_type: str = "chance") -> Optional[Dict[str, Any]]:
        if deck_type not in self.decks or not self.decks[deck_type]:
            return None

        card = self.decks[deck_type].pop(0)
        # Thẻ bình thường -> đưa xuống cuối
        if card["action"] != "get_out_of_jail_card":
            self.decks[deck_type].append(card)
        return card

    # ======================================================
    # 4️⃣ ÁP DỤNG HIỆU ỨNG (CHỈ TẠO INSTRUCTION)
    # ======================================================
    def apply_effect(self, card: Dict[str, Any], player: 'Player', board: 'Board', all_players: List['Player']):
        fn = card.get("effect_fn")
        if not fn:
            return {"action": "none", "message": "No effect function found."}

        return fn(card, player, board, all_players)

    # ======================================================
    # 5️⃣ HANDLER CÁC LOẠI THẺ — CHỈ TRẢ VỀ INSTRUCTION
    # ======================================================

    def _handle_move_to(self, card, player, board, all_players):
        return {
            "action": "move_to",
            "target_position": card.get("target"),
            "reward_if_pass_go": card.get("reward_if_pass_go", 0),
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_move_back(self, card, player, board, all_players):
        return {
            "action": "move_back",
            "steps": card.get("steps", 3),
            "player_id": player.id,
            "message": f"Move back {card.get('steps', 3)} spaces. {card['text']}"
        }

    def _handle_nearest_utility(self, card, player, board, all_players):
        nearest = board.find_nearest_tile(player.position, "utility")
        return {
            "action": "move_to_and_pay_special_rent",
            "target_position": nearest,
            "multiplier": card.get("multiplier", 10),
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_nearest_railroad(self, card, player, board, all_players):
        nearest = board.find_nearest_tile(player.position, "railroad")
        return {
            "action": "move_to_and_pay_special_rent",
            "target_position": nearest,
            "multiplier": card.get("multiplier", 2),
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_go_to_jail(self, card, player, board, all_players):
        jail_tile = board.get_jail_tile()
        return {
            "action": "go_to_jail",
            "jail_position": jail_tile.position,
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_earn(self, card, player, board, all_players):
        return {
            "action": "earn",
            "amount": card["amount"],
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_pay(self, card, player, board, all_players):
        return {
            "action": "pay_bank",
            "amount": card["amount"],
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_pay_others(self, card, player, board, all_players):
        target_ids = [p.id for p in all_players if p.id != player.id]
        return {
            "action": "transfer_to_all",
            "sender_id": player.id,
            "target_ids": target_ids,
            "amount": card["amount"],
            "message": card["text"]
        }

    def _handle_collect_from_others(self, card, player, board, all_players):
        source_ids = [p.id for p in all_players if p.id != player.id]
        return {
            "action": "collect_from_all",
            "receiver_id": player.id,
            "source_ids": source_ids,
            "amount": card["amount"],
            "message": card["text"]
        }

    def _handle_property_repair(self, card, player, board, all_players):
        return {
            "action": "property_repair",
            "player_id": player.id,
            "house_cost": card.get("cost_per_house", 0),
            "hotel_cost": card.get("cost_per_hotel", 0),
            "message": card["text"]
        }

    def _handle_get_out_of_jail_card(self, card, player, board, all_players):
        return {
            "action": "give_jail_card",
            "player_id": player.id,
            "message": card["text"]
        }

    def _handle_default(self, card, player, board, all_players):
        return {
            "action": "none",
            "player_id": player.id,
            "message": card["text"]
        }
