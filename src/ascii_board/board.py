# src/ascii_board/board.py
"""
Board (ASCII Renderer) — fixed perimeter mapping + API gameplay cơ bản

NOTE:
  Giờ ta build mapping 0..39 bằng cách đi quanh viền 11x11 theo đúng thứ tự.
- Board quản lý:
  + Danh sách ô (tiles)
  + Chủ sở hữu (ownership)
  + Nhà/khách sạn (buildings)
  + Render ASCII để test.
"""

from typing import Dict, List
from src.ascii_board.tiles import TILES

GRID = 11               # 11x11 cells (chỉ dùng viền ngoài)
TILE_W, TILE_H = 11, 5  # kích thước ASCII 1 ô

# ---------- Build mapping index -> (x,y) ----------
def _build_perimeter_positions(grid: int = GRID):
    """Trả về list 40 tọa độ [(x,y)] cho index 0..39
       đi NGƯỢC kim đồng hồ từ GO (0) ở góc dưới-phải."""
    maxv = grid - 1
    pos = []

    # 0: GO (bottom-right)
    pos.append((maxv, maxv))

    # 1..9: đi sang TRÁI cạnh dưới
    for x in range(maxv - 1, 0, -1):
        pos.append((x, maxv))

    # 10: Jail (bottom-left)
    pos.append((0, maxv))

    # 11..19: đi LÊN cạnh trái
    for y in range(maxv - 1, 0, -1):
        pos.append((0, y))

    # 20: Free Parking (top-left)
    pos.append((0, 0))

    # 21..29: đi sang PHẢI cạnh trên
    for x in range(1, maxv):
        pos.append((x, 0))

    # 30: Go To Jail (top-right)
    pos.append((maxv, 0))

    # 31..39: đi XUỐNG cạnh phải
    for y in range(1, maxv):
        pos.append((maxv, y))

    assert len(pos) == 40
    return pos

# mapping forward & reverse
_PERIM = _build_perimeter_positions()
_COORD2IDX: Dict[tuple[int, int], int] = {xy: i for i, xy in enumerate(_PERIM)}

def _tile_index_at(x: int, y: int) -> int:
    """Tra cứu index 0..39 nếu (x,y) nằm trên viền, ngược lại -1."""
    return _COORD2IDX.get((x, y), -1)

# ---------- Utils ----------
def _pad_center(s: str, w: int) -> str:
    s = s[:w]
    left = (w - len(s)) // 2
    return " " * left + s + " " * (w - len(s) - left)

# ---------- Class Board ----------
class Board:
    """Quản lý bàn cờ Monopoly (40 ô) + API cơ bản + render ASCII."""

    # 1. init
    def __init__(self, tile_w: int = TILE_W, tile_h: int = TILE_H):
        self.tw, self.th = tile_w, tile_h
        self.W = GRID * self.tw + 1
        self.H = GRID * self.th + 1

        self.tiles: List[str] = self._init_tiles()
        self.ownership: Dict[int, str] = {}
        self.buildings: Dict[int, Dict[str, int | bool]] = {}

    # 2. _init_tiles
    def _init_tiles(self) -> List[str]:
        """Private: trả về danh sách tên ô (40 ô)."""
        return TILES

    # 3. get_tile
    def get_tile(self, position: int) -> str:
        """Trả về tên ô theo index."""
        return self.tiles[position % 40]

    # 4. get_next_position
    def get_next_position(self, current: int, steps: int) -> int:
        """Tính vị trí mới sau khi di chuyển steps."""
        return (current + steps) % 40

    # 5. set_owner
    def set_owner(self, position: int, player: str) -> None:
        """Gán chủ sở hữu cho 1 ô."""
        self.ownership[position % 40] = player

    # 6. get_all_properties
    def get_all_properties(self) -> Dict[int, str]:
        """Trả về dict copy các ô đã có chủ."""
        return dict(self.ownership)

    # 7. check_tile_action
    def check_tile_action(self, position: int) -> str:
        """Phân loại ô để xử lý hành động."""
        idx = position % 40
        name = self.get_tile(idx)

        if idx == 0: return "GO"
        if idx == 20: return "FREE"
        if idx == 30: return "GOTO_JAIL"
        if "Jail" in name: return "JAIL"
        if "Tax" in name: return "TAX"
        if "Chance" in name or "Community" in name: return "CARD"
        if "Railroad" in name or "RR" in name: return "RAILROAD"
        if "Company" in name or "Works" in name: return "UTILITY"
        return "PROPERTY"

    # 8. render_ascii
    def render_ascii(self, state: Dict) -> str:
        """
        Hiển thị bàn cờ ASCII.
        state: 
          players   [{nick, pos}]
          ownership {tile -> owner}
          buildings {tile -> {houses, hotel}}
        """
        ownership = state.get("ownership", self.ownership)
        buildings = state.get("buildings", self.buildings)

        canvas: List[List[str]] = [[" "] * self.W for _ in range(self.H)]

        def draw_cell(cx: int, cy: int, lines: List[str]):
            x0, y0 = cx * self.tw, cy * self.th
            # vẽ khung
            for i in range(self.tw + 1):
                ch = "-" if 0 < i < self.tw else "+"
                canvas[y0][x0 + i] = ch
                canvas[y0 + self.th][x0 + i] = ch
            for j in range(self.th + 1):
                ch = "|" if 0 < j < self.th else "+"
                canvas[y0 + j][x0] = ch
                canvas[y0 + j][x0 + self.tw] = ch

            inner_w = self.tw - 1
            for k, raw in enumerate(lines[:4]):
                text = _pad_center(raw or "", inner_w)
                for i, c in enumerate(text):
                    canvas[y0 + 1 + k][x0 + 1 + i] = c

        # group players by tile
        players_at: Dict[int, List[str]] = {}
        for p in state.get("players", []):
            players_at.setdefault(p["pos"] % 40, []).append(p["nick"])

        # vẽ các ô
        for y in range(GRID):
            for x in range(GRID):
                idx = _tile_index_at(x, y)
                if idx < 0:
                    continue
                name = self.tiles[idx]
                owner = ownership.get(idx, "")
                binfo = buildings.get(idx, {"houses": 0, "hotel": False})
                builds = "HOTEL" if binfo.get("hotel") else ("H" * min(4, int(binfo.get("houses", 0))))
                ppl = "".join(players_at.get(idx, []))[:8]

                lines = [name, f"Own:{owner}" if owner else "", builds, ppl]
                draw_cell(x, y, lines)

        return "\n".join("".join(row) for row in canvas)
def main () :
    demo_state = {
        # Danh sách người chơi với vị trí hiện tại
        # 0 = GO (góc dưới-phải)
        # 10 = Jail / Just Visiting (góc dưới-trái)
        # 20 = Free Parking (góc trên-trái)
        # 30 = Go To Jail (góc trên-phải)
        "players": [
            {"nick": "A", "pos": 0},  # A đứng ở GO (góc dưới-phải)
            {"nick": "B", "pos": 10},  # B đứng ở Jail (góc dưới-trái)
            {"nick": "C", "pos": 24},  # C đứng ở Illinois Ave (cạnh trên, giữa)
            {"nick": "D", "pos": 39},  # D đứng ở Boardwalk (ngay trước GO, cạnh phải)
        ],

        # Sở hữu đất: tileIndex -> tên player
        "ownership": {
            1: "A",  # Mediterranean Ave thuộc A
            3: "B",  # Baltic Ave thuộc B
            6: "C",  # Oriental Ave thuộc C
            8: "D",  # Vermont Ave thuộc D
            39: "A"  # Boardwalk thuộc A
        },

        # Thông tin nhà/khách sạn: tileIndex -> {houses: n, hotel: bool}
        "buildings": {
            1: {"houses": 2, "hotel": False},  # Mediterranean có 2 nhà
            39: {"houses": 0, "hotel": True},  # Boardwalk có 1 khách sạn
        },
    }
    # Tạo board và in ra bản đồ ASCII dựa vào demo_state
    board = Board()
    print(board.render_ascii(demo_state))

if __name__ == "__main__":

     main()