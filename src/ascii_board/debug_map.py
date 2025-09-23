
"""
Script dùng để kiểm tra mapping 0..39 quanh viền 11x11 có đủ và không bị trùng lặp.
Cách chạy:
    python -m src.ascii_board.debug_map
"""

# Debug mapping for the 11x11 board border
GRID = 11
from .board import _tile_index_at  

def print_index_grid():
    maxv = GRID - 1
    # in header
    print("    " + " ".join(f"{x:>3}" for x in range(GRID)))
    for y in range(GRID):
        row = []
        for x in range(GRID):
            idx = _tile_index_at(x, y)
            row.append(f"{idx:>3}" if idx >= 0 else "  .")
        print(f"y={y:>2} " + " ".join(row))

def check_border_integrity():
    seen = {}
    border_indices = []
    for y in range(GRID):
        for x in range(GRID):
            idx = _tile_index_at(x, y)
            if idx >= 0:
                if idx in seen:
                    print(f"[DUP] idx={idx} trùng: ({seen[idx][0]},{seen[idx][1]}) và ({x},{y})")
                else:
                    seen[idx] = (x, y)
                border_indices.append(idx)

    # kiểm tra đủ 40 ô và đúng corners
    print(f"Border count = {len(border_indices)} (unique={len(set(border_indices))})")
    print("Corners:",
          " GO(0)@", seen.get(0),
          " Jail(10)@", seen.get(10),
          " Free(20)@", seen.get(20),
          " GoToJail(30)@", seen.get(30))

    # thiếu/sai index nào?
    missing = [i for i in range(40) if i not in seen]
    if missing:
        print("[MISS]", missing)
    else:
        print("[OK] Đủ 0..39, không thiếu.")

if __name__ == "__main__":
    print_index_grid()
    print("-" * 60)
    check_border_integrity()
