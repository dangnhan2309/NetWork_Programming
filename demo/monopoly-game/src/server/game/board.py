"""
Board logic for Monopoly
-----------------------------------
Quản lý các ô (tile), loại tài sản, giá, tiền thuê,
và các quy tắc liên quan đến sở hữu & tiền thuê.
"""

from typing import Dict, List, Optional


class Board:
    def __init__(self):
        self.tiles = self._create_tiles()

    # ======================================
    # Tạo danh sách 40 ô Monopoly cơ bản
    # ======================================
    def _create_tiles(self) -> List[Dict]:
        tiles = []
        property_names = [
            "Mediterranean Ave", "Baltic Ave", "Oriental Ave", "Vermont Ave",
            "Connecticut Ave", "St. Charles Place", "States Ave", "Virginia Ave",
            "St. James Place", "Tennessee Ave", "New York Ave", "Kentucky Ave",
            "Indiana Ave", "Illinois Ave", "Atlantic Ave", "Ventnor Ave",
            "Marvin Gardens", "Pacific Ave", "North Carolina Ave", "Pennsylvania Ave",
            "Park Place", "Boardwalk"
        ]
        property_positions = [1, 3, 6, 8, 9, 11, 13, 14, 16, 18, 19,
                              21, 23, 24, 26, 27, 29, 31, 32, 34, 37, 39]
        base_prices = [60, 60, 100, 100, 120, 140, 140, 160, 180, 180, 200,
                       220, 220, 240, 260, 260, 280, 300, 300, 320, 350, 400]
        base_rents = [2, 4, 6, 6, 8, 10, 10, 12, 14, 14, 16,
                      18, 18, 20, 22, 22, 24, 26, 26, 28, 35, 50]
        color_groups = [
            "Brown", "Brown", "Light Blue", "Light Blue", "Light Blue",
            "Pink", "Pink", "Pink", "Orange", "Orange", "Orange",
            "Red", "Red", "Red", "Yellow", "Yellow", "Yellow",
            "Green", "Green", "Green", "Dark Blue", "Dark Blue"
        ]

        for i in range(40):
            if i == 0:
                tiles.append({"id": i, "name": "GO", "type": "go", "price": 0})
            elif i == 10:
                tiles.append({"id": i, "name": "Jail", "type": "jail", "price": 0})
            elif i == 20:
                tiles.append({"id": i, "name": "Free Parking", "type": "free_parking", "price": 0})
            elif i == 30:
                tiles.append({"id": i, "name": "Go to Jail", "type": "go_to_jail", "price": 0})
            elif i in [2, 17, 33]:
                tiles.append({"id": i, "name": "Chance", "type": "chance", "price": 0})
            elif i in [7, 22, 36]:
                tiles.append({"id": i, "name": "Community Chest", "type": "community_chest", "price": 0})
            elif i in [4, 38]:
                tiles.append({
                    "id": i,
                    "name": "Income Tax" if i == 4 else "Luxury Tax",
                    "type": "tax",
                    "amount": 200 if i == 4 else 100
                })
            elif i in [5, 15, 25, 35]:
                tiles.append({
                    "id": i,
                    "name": f"Railroad {i//10 + 1}",
                    "type": "railroad",
                    "price": 200,
                    "rent": 25,
                    "owner": None
                })
            elif i in [12, 28]:
                tiles.append({
                    "id": i,
                    "name": "Electric Company" if i == 12 else "Water Works",
                    "type": "utility",
                    "price": 150,
                    "owner": None
                })
            elif i in property_positions:
                idx = property_positions.index(i)
                tiles.append({
                    "id": i,
                    "name": property_names[idx],
                    "type": "property",
                    "price": base_prices[idx],
                    "rent": base_rents[idx],
                    "group": color_groups[idx],
                    "owner": None,
                    "houses": 0
                })
            else:
                tiles.append({"id": i, "name": f"Tile {i}", "type": "special"})
        return tiles

    # ======================================
    # Hàm tiện ích
    # ======================================

    def get_tile(self, tile_id: int) -> Optional[Dict]:
        """Lấy thông tin ô theo vị trí"""
        if 0 <= tile_id < len(self.tiles):
            return self.tiles[tile_id]
        return None

    def is_property(self, tile: Dict) -> bool:
        """Kiểm tra ô là loại có thể mua"""
        return tile["type"] in ("property", "railroad", "utility")

    def next_position(self, current_pos: int, steps: int) -> int:
        """Tính vị trí mới khi di chuyển"""
        return (current_pos + steps) % len(self.tiles)

    # ======================================
    # Logic sở hữu & tiền thuê
    # ======================================

    def buy_property(self, tile_id: int, player_id: str) -> bool:
        """Đánh dấu quyền sở hữu ô"""
        tile = self.get_tile(tile_id)
        if not tile or not self.is_property(tile):
            return False
        if tile.get("owner") is not None:
            return False
        tile["owner"] = player_id
        return True

    def reset_owner(self, player_id: str):
        """Xóa quyền sở hữu của người chơi (khi bankrupt)"""
        for tile in self.tiles:
            if tile.get("owner") == player_id:
                tile["owner"] = None

    def get_group_properties(self, group_name: str) -> List[Dict]:
        """Trả về danh sách ô cùng nhóm màu"""
        return [t for t in self.tiles if t.get("group") == group_name]

    def get_rent(self, tile_id: int, dice_roll: Optional[int] = None) -> int:
        """Tính tiền thuê dựa trên loại tài sản"""
        tile = self.get_tile(tile_id)
        if not tile or not self.is_property(tile):
            return 0

        ttype = tile["type"]
        if ttype == "property":
            # Nếu người chơi sở hữu cả nhóm màu → tiền thuê gấp đôi
            group = tile.get("group")
            group_tiles = self.get_group_properties(group)
            if group_tiles and all(t.get("owner") == tile.get("owner") for t in group_tiles):
                return tile["rent"] * 2
            return tile["rent"]

        elif ttype == "railroad":
            # Tiền thuê dựa trên số railroad sở hữu
            owner = tile.get("owner")
            railroads = [t for t in self.tiles if t["type"] == "railroad" and t.get("owner") == owner]
            return 25 * (2 ** (len(railroads) - 1))  # 25, 50, 100, 200

        elif ttype == "utility":
            # Tiền thuê dựa trên xúc xắc
            owner = tile.get("owner")
            utilities = [t for t in self.tiles if t["type"] == "utility" and t.get("owner") == owner]
            multiplier = 4 if len(utilities) == 1 else 10
            return (dice_roll or 0) * multiplier

        return 0
