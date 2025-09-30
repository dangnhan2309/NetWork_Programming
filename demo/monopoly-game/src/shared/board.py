 
# src/ascii_board/board.py
"""
Board (ASCII Renderer) — fixed perimeter mapping

NOTE:
- Trước đây lỗi "Jail / Just Visiting" bị in 2 lần do logic _tile_index_at()
  xử lý góc rồi vẫn rơi vào nhánh cạnh. Ở bản này, ta tạo MAPPING RÕ RÀNG
  cho 40 chỉ số (0..39) bằng cách "đi bộ quanh viền" 11x11 theo đúng thứ tự
  Monopoly, rồi tra cứu ngược (coord -> index). Nhờ vậy KHÔNG còn khả năng
  trùng lặp giữa corner/edge.



- Quy ước vị trí (đi NGƯỢC kim đồng hồ từ GO):
  GRID = 11  => tọa độ (x, y) với x,y ∈ [0..10]
  0  (GO)        @ (10,10)  góc dưới-phải
  10 (Jail)      @ (0,10)   góc dưới-trái
  20 (Free)      @ (0,0)    góc trên-trái
  30 (GoToJail)  @ (10,0)   góc trên-phải
"""

from typing import Dict, List
from .tiles import TILES

GRID = 11               # 11x11 cells (only the border is used)
TILE_W, TILE_H = 11, 5  # size of one ASCII cell

# ---------- Perimeter Mapping (build once, no if-else mistakes) ----------
def _build_perimeter_positions(grid: int = GRID):
    """Trả về list 40 tọa độ [(x,y)] cho index 0..39
       đi NGƯỢC kim đồng hồ từ GO (0) ở góc dưới-phải."""
    maxv = grid - 1
    pos = []

    # 0: GO (bottom-right)
    pos.append((maxv, maxv))

    # 1..9: sang TRÁI cạnh dưới
    for x in range(maxv - 1, 0, -1):  # 9..1
        pos.append((x, maxv))

    # 10: Jail / Just Visiting (bottom-left)
    pos.append((0, maxv))

    # 11..19: đi LÊN cạnh trái
    for y in range(maxv - 1, 0, -1):  # 9..1
        pos.append((0, y))

    # 20: Free Parking (top-left)
    pos.append((0, 0))

    # 21..29: đi SANG PHẢI cạnh trên
    for x in range(1, maxv):  # 1..9
        pos.append((x, 0))

    # 30: Go To Jail (top-right)
    pos.append((maxv, 0))

    # 31..39: đi XUỐNG cạnh phải
    for y in range(1, maxv):  # 1..9
        pos.append((maxv, y))

    assert len(pos) == 40
    return pos

# Build forward (index -> coord) và reverse (coord -> index)
_PERIM = _build_perimeter_positions()
_COORD2IDX: Dict[tuple[int, int], int] = {xy: i for i, xy in enumerate(_PERIM)}

def _tile_index_at(x: int, y: int) -> int:
    """Tra cứu index 0..39 nếu (x,y) nằm trên viền; ngược lại trả -1."""
    return _COORD2IDX.get((x, y), -1)

# ------------------------ Rendering utilities ----------------------------
def _pad_center(s: str, w: int) -> str:
    s = s[:w]
    left = (w - len(s)) // 2
    return " " * left + s + " " * (w - len(s) - left)

class Board:
    """Renderer cho Monopoly ASCII (viền 11x11, 40 ô)."""

    def __init__(self, tile_w: int = TILE_W, tile_h: int = TILE_H):
        self.tw, self.th = tile_w, tile_h
        self.W = GRID * self.tw + 1
        self.H = GRID * self.th + 1

    def render_ascii(self, state: Dict) -> str:
        """
        state:
          players:   [{nick:str, pos:int}, ...]
          ownership: {tileIndex:int -> ownerNick:str}
          buildings: {tileIndex:int -> {houses:int, hotel:bool}}
        """
        canvas: List[List[str]] = [[" "] * self.W for _ in range(self.H)]

        def draw_cell(cx: int, cy: int, lines: List[str]):
            x0, y0 = cx * self.tw, cy * self.th
            # khung ô: +---+ |   |
            for i in range(self.tw + 1):
                ch = "-" if 0 < i < self.tw else "+"
                canvas[y0][x0 + i] = ch
                canvas[y0 + self.th][x0 + i] = ch
            for j in range(self.th + 1):
                ch = "|" if 0 < j < self.th else "+"
                canvas[y0 + j][x0] = ch
                canvas[y0 + j][x0 + self.tw] = ch

            inner_w = self.tw - 1
            for k, raw in enumerate(lines[:4]):  # hiển thị tối đa 4 dòng
                text = _pad_center(raw, inner_w)
                for i, c in enumerate(text):
                    canvas[y0 + 1 + k][x0 + 1 + i] = c

        # gom người chơi theo tile
        players_at: Dict[int, List[str]] = {}
        for p in state.get("players", []):
            players_at.setdefault(p["pos"], []).append(p["nick"])

        for y in range(GRID):
            for x in range(GRID):
                idx = _tile_index_at(x, y)
                if idx < 0:
                    continue
                name = TILES[idx] if idx < len(TILES) else f"T{idx}"
                owner = state.get("ownership", {}).get(idx, "")
                binfo = state.get("buildings", {}).get(idx, {"houses": 0, "hotel": False})
                builds = "HOTEL" if binfo.get("hotel") else ("H" * min(4, binfo.get("houses", 0)))
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