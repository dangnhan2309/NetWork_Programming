import json
from typing import Dict, List, Optional
import json 

TILE_WIDTH = 11
TILE_HEIGHT = 7

class Board:
    def __init__(self, json_path: str = "board_tiles.json"):
        self.tiles = self.load_tiles_from_json(json_path)

    def load_tiles_from_json(self, path: str) -> List[Dict]:
        """Load board tiles from JSON file"""
        with open(path, "r", encoding="utf-8") as f:
            tiles = json.load(f)
        return tiles

    def fit_text(self, text: str, width: int) -> str:
        if len(text) > width:
            return text[:width-2] + ".."
        return text.center(width)

    def create_tile_lines(self, tile: Dict, pos: int, players: Dict[str, int]) -> List[str]:
        colors = {
            "property": "\033[42m", "railroad": "\033[44m", "utility": "\033[46m",
            "tax": "\033[41m", "chance": "\033[43m", "community_chest": "\033[45m",
            "go": "\033[47m", "jail": "\033[47m", "free_parking": "\033[47m",
            "go_to_jail": "\033[47m", "special": "\033[47m"
        }
        color = colors.get(tile.get("type", "special"), "\033[47m")
        reset = "\033[0m"

        occupants = [name[0].upper() for name, p in players.items() if p == pos]
        player_str = "".join(occupants) if occupants else " "

        name = self.fit_text(tile.get("name", ""), 9)
        type_display = tile.get("type", "special")[:7]
        price_str = f"${tile.get('price', '')}" if tile.get("price") else ""

        lines = [
            color + "┌" + "─"*9 + "┐" + reset,
            color + f"│{str(pos).center(9)}│" + reset,
            color + f"│{name}│" + reset,
            color + f"│{type_display.center(9)}│" + reset,
            color + f"│{price_str.center(9)}│" + reset,
            color + f"│[{player_str}]".ljust(10) + "│" + reset,
            color + "└" + "─"*9 + "┘" + reset
        ]
        return lines

    def render_board(self, players: Dict[str, int] = None):
        if players is None:
            players = {}

        # Cạnh dưới: 0 -> 10
        bottom_row = [self.create_tile_lines(self.tiles[i], i, players) for i in range(0, 11)]
        # Cạnh phải: 11 -> 19
        right_col = [self.create_tile_lines(self.tiles[i], i, players) for i in range(11, 20)]
        right_col.reverse()
        # Cạnh trên: 20 -> 30
        top_row = [self.create_tile_lines(self.tiles[i], i, players) for i in range(20, 31)]
        top_row.reverse()
        # Cạnh trái: 31 -> 39
        left_col = [self.create_tile_lines(self.tiles[i], i, players) for i in range(31, 40)]

        # ===== VẼ BOARD =====
        # Cạnh trên
        for line_num in range(7):
            print("".join(tile[line_num] for tile in top_row))

        # Hai cạnh dọc
        for i in range(len(right_col)):
            left_tile = left_col[i]
            right_tile = right_col[i]
            middle_space = " " * (TILE_WIDTH * 9)
            for ln in range(7):
                print(left_tile[ln] + middle_space + right_tile[ln])

        # Cạnh dưới
        for line_num in range(7):
            print("".join(tile[line_num] for tile in bottom_row))

        # ===== CHÚ THÍCH =====
        print("\n📝 CHÚ THÍCH:")
        print("🟩 Property  🟦 Railroad  🟨 Chance  🟪 C.Chest  🟥 Tax  ⬜️ Special")
        if players:
            player_list = [f"{name}[{name[0]}]" for name in players.keys()]
            print(f"👥 NGƯỜI CHƠI: {', '.join(player_list)}")