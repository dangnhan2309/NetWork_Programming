# src/ascii_board/board.py
from typing import Dict, List
from .tiles import TILES

GRID = 11               # 11x11 ô (chỉ vẽ viền)
TILE_W, TILE_H = 11, 5  # kích thước 1 ô (ký tự)

def _tile_index_at(x: int, y: int) -> int:
    """Map (x,y) trên viền 11x11 -> index 0..39; còn lại -1.
    Góc quy ước:
      (max,max)=0 GO; (max,0)=10 Jail; (0,0)=20 Free; (0,max)=30 Go2Jail
    """
    maxv = GRID - 1
    # corners
    if x == maxv and y == maxv: return 0
    if x == maxv and y == 0:   return 10
    if x == 0   and y == 0:    return 20
    if x == 0   and y == maxv: return 30
    # right edge (exclude corners): bottom->top => 1..9
    if x == maxv and 0 < y < maxv:
        return 1 + (maxv - y)
    # top edge: right->left => 11..19
    if y == 0 and 0 < x < maxv:
        return 10 + (maxv - x)
    # left edge: top->bottom => 21..29
    if x == 0 and 0 < y < maxv:
        return 20 + y
    # bottom edge: left->right => 31..39
    if y == maxv and 0 < x < maxv:
        return 30 + x
    return -1

def _pad_center(s: str, w: int) -> str:
    s = s[:w]
    left = (w - len(s)) // 2
    return " " * left + s + " " * (w - len(s) - left)

class Board:
    """Renderer cho Monopoly ASCII."""
    def __init__(self, tile_w=TILE_W, tile_h=TILE_H):
        self.tw, self.th = tile_w, tile_h
        self.W = GRID * self.tw + 1
        self.H = GRID * self.th + 1

    def render_ascii(self, state: Dict) -> str:
        """
        state:
          players: [{nick:'A', pos:int}, ...]
          ownership: {tileIndex:'A'|'B'|'C'|'D'}
          buildings: {tileIndex:{houses:int, hotel:bool}}
        """
        canvas: List[List[str]] = [[" "] * self.W for _ in range(self.H)]

        def draw_cell(cx: int, cy: int, lines: List[str]):
            x0, y0 = cx * self.tw, cy * self.th
            # khung: +---+ |   |
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
