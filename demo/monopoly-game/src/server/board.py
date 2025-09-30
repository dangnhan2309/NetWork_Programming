"""
Board class cho Monopoly game
"""

from typing import Dict, List

TILE_WIDTH = 11
TILE_HEIGHT = 7

class Board:
    def __init__(self):
        self.tiles = self._create_tiles()
        
    def _create_tiles(self) -> List[Dict]:
        """Tạo danh sách 40 ô trên board"""
        tiles = []
        for i in range(40):
            if i == 0:
                tiles.append({"name": "GO", "type": "go", "owner": None, "price": 0, "rent": 0})
            elif i == 10:
                tiles.append({"name": "Jail", "type": "jail", "owner": None, "price": 0, "rent": 0})
            elif i == 20:
                tiles.append({"name": "Free Parking", "type": "free_parking", "owner": None, "price": 0, "rent": 0})
            elif i == 30:
                tiles.append({"name": "Go to Jail", "type": "go_to_jail", "owner": None, "price": 0, "rent": 0})
            elif i in [2, 17, 33]:
                tiles.append({"name": "Chance", "type": "chance", "owner": None, "price": 0, "rent": 0})
            elif i in [7, 22, 36]:
                tiles.append({"name": "Community Chest", "type": "community_chest", "owner": None, "price": 0, "rent": 0})
            elif i in [4, 38]:
                tiles.append({"name": "Income Tax" if i == 4 else "Luxury Tax", "type": "tax", "owner": None, "price": 0, "rent": 0, "amount": 200 if i==4 else 100})
            elif i in [5, 15, 25, 35]:
                tiles.append({"name": f"Railroad {i//10 + 1}", "type": "railroad", "owner": None, "price": 200, "rent": 25})
            elif i in [12, 28]:
                tiles.append({"name": "Electric Company" if i == 12 else "Water Works", "type": "utility", "owner": None, "price": 150, "rent": 4})
            else:
                property_names = [
                    "Mediterranean Ave", "Baltic Ave", "Oriental Ave", "Vermont Ave",
                    "Connecticut Ave", "St. Charles Place", "States Ave", "Virginia Ave",
                    "St. James Place", "Tennessee Ave", "New York Ave", "Kentucky Ave",
                    "Indiana Ave", "Illinois Ave", "Atlantic Ave", "Ventnor Ave",
                    "Marvin Gardens", "Pacific Ave", "North Carolina Ave", "Pennsylvania Ave",
                    "Park Place", "Boardwalk"
                ]
                property_positions = [1, 3, 6, 8, 9, 11, 13, 14, 16, 18, 19, 21, 23, 24, 26, 27, 29, 31, 32, 34, 37, 39]
                base_prices = [60, 60, 100, 100, 120, 140, 140, 160, 180, 180, 200, 220, 220, 240, 260, 260, 280, 300, 300, 320, 350, 400]
                base_rents = [2, 4, 6, 6, 8, 10, 10, 12, 14, 14, 16, 18, 18, 20, 22, 22, 24, 26, 26, 28, 35, 50]

                if i in property_positions:
                    idx = property_positions.index(i)
                    tiles.append({"name": property_names[idx], "type": "property", "owner": None, "price": base_prices[idx], "rent": base_rents[idx]})
                else:
                    tiles.append({"name": f"Tile {i}", "type": "special", "owner": None, "price": 0, "rent": 0})
        return tiles

    def get_tile(self, pos: int) -> Dict:
        if 0 <= pos < len(self.tiles):
            return self.tiles[pos]
        return {"name": "Invalid", "type": "invalid", "owner": None, "price": 0, "rent": 0}

    def fit_text(self, text, width):
        if len(text) > width:
            return text[:width-2] + ".."
        return text.center(width)

    def create_tile_lines(self, tile, pos, players):
        colors = {
            "property": "\033[42m", "railroad": "\033[44m", "utility": "\033[46m",
            "tax": "\033[41m", "chance": "\033[43m", "community_chest": "\033[45m",
            "go": "\033[47m", "jail": "\033[47m", "free_parking": "\033[47m",
            "go_to_jail": "\033[47m", "special": "\033[47m"
        }
        color = colors.get(tile["type"], "\033[47m")
        reset = "\033[0m"

        occupants = [name[0].upper() for name, p in players.items() if p == pos]
        player_str = "".join(occupants) if occupants else " "

        name = self.fit_text(tile["name"], TILE_WIDTH-2)
        type_display = tile['type'][:TILE_WIDTH-2] if tile['type'] != 'community_chest' else "C.Chest"
        price_str = f"${tile['price']}" if tile.get('price', 0) > 0 else ""

        lines = []
        lines.append(color + "┌" + "─"*(TILE_WIDTH-2) + "┐" + reset)
        lines.append(color + f"│{str(pos).center(TILE_WIDTH-2)}│" + reset)
        lines.append(color + f"│{name}│" + reset)
        lines.append(color + f"│{type_display.center(TILE_WIDTH-2)}│" + reset)
        lines.append(color + f"│{price_str.center(TILE_WIDTH-2)}│" + reset)
        lines.append(color + f"│[{player_str}]".ljust(TILE_WIDTH-1) + "│" + reset)
        lines.append(color + "└" + "─"*(TILE_WIDTH-2) + "┘" + reset)
        return lines

    def render_board(self, players: Dict[str, int] = None):
        if players is None:
            players = {}

        # Cạnh dưới 0-10
        bottom_row = [self.create_tile_lines(self.tiles[i], i, players) for i in range(0,11)]
        # Cạnh trái 11-19
        left_col = [self.create_tile_lines(self.tiles[i], i, players) for i in range(11,20)]
        # Cạnh trên 20-30 ngược
        top_row = [self.create_tile_lines(self.tiles[i], i, players) for i in range(20,31)][::-1]
        # Cạnh phải 31-39
        right_col = [self.create_tile_lines(self.tiles[i], i, players) for i in range(31,40)]

        # Vẽ cạnh trên
        for line_num in range(TILE_HEIGHT):
            line = ""
            for tile in top_row:
                line += tile[line_num]
            print(line)

        # Vẽ phần giữa (cạnh trái + khoảng trống + cạnh phải)
        for i in range(len(left_col)):
            for ln in range(TILE_HEIGHT):
                left_line = left_col[i][ln]
                right_line = right_col[i][ln]
                middle = " " * (TILE_WIDTH*9)  # khoảng trống
                print(left_line + middle + right_line)

        # Vẽ cạnh dưới
        for line_num in range(TILE_HEIGHT):
            line = ""
            for tile in bottom_row:
                line += tile[line_num]
            print(line)

        # Chú thích
        print("\nLEGEND:")
        print("🟩 Property  🟦 Railroad  🟨 Chance  🟪 C.Chest  🟥 Tax  ⬜️ Special")
        if players:
            player_list = [f"{name}[{name[0]}]" for name in players.keys()]
            print(f"PLAYERS: {', '.join(player_list)}")

    def display_tile_info(self, position: int):
        tile = self.get_tile(position)
        print(f"\n📍 Tile {position}: {tile['name']}")
        print(f"   Type: {tile['type']}")
        if tile['type'] in ['property', 'railroad', 'utility']:
            print(f"   Price: ${tile.get('price',0)}")
            print(f"   Rent: ${tile.get('rent',0)}")
            owner = tile.get('owner')
            print(f"   Owner: {owner if owner else 'Bank'}")
        elif tile['type'] == 'tax':
            print(f"   Tax Amount: ${tile.get('amount',0)}")

# Demo sử dụng
if __name__ == "__main__":
    board = Board()
    demo_players = {"Player1":0, "Player2":5, "Player3":15, "Player4":25}
    board.render_board(demo_players)
    board.display_tile_info(1)
    board.display_tile_info(5)
