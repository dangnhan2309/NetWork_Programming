"""
Demo: Vẽ bàn cờ Monopoly ASCII
--------------------------------
File này dùng để test hiển thị board ASCII 
Không liên quan đến logic game, chỉ để kiểm chứng:
    - Mapping 40 ô (0..39) có đúng vị trí không.
    - Người chơi (players) đứng ở ô nào thì hiển thị đúng.
    - Sở hữu đất (ownership) và nhà/khách sạn (buildings) có in ra hay không.

Cách chạy:
    python -m src.ascii_board.demo_board

Kết quả:
    In ra bàn cờ ASCII 11x11 viền ngoài, có tên ô, người chơi, và thông tin sở hữu.
"""

# Import class Board từ file board.py
from .board import Board

# Trạng thái demo để test hiển thị board
demo_state = {
    # Danh sách người chơi với vị trí hiện tại (0=GO, 10=Jail, 20=Free Parking, 30=Go To Jail)
    "players": [
        {"nick": "A", "pos": 0},     # A đứng ở GO
        {"nick": "B", "pos": 10},    # B đứng ở Jail
        {"nick": "C", "pos": 24},    # C đứng ở Illinois (trên cạnh trái)
        {"nick": "D", "pos": 39},    # D đứng ở Boardwalk (ngay trước GO)
    ],

    # Sở hữu đất: tileIndex -> tên player
    "ownership": {
        1: "A",   # Mediterranean Ave thuộc A
        3: "B",   # Baltic Ave thuộc B
        6: "C",   # Oriental Ave thuộc C
        8: "D",   # Vermont Ave thuộc D
        39: "A"   # Boardwalk thuộc A
    },

    # Thông tin nhà/khách sạn: tileIndex -> {houses: n, hotel: bool}
    "buildings": {
        1: {"houses": 2, "hotel": False},   # Mediterranean có 2 nhà
        39: {"houses": 0, "hotel": True},   # Boardwalk có 1 khách sạn
    },
}

if __name__ == "__main__":
    # Tạo board và in ra bản đồ ASCII dựa vào demo_state
    board = Board()
    print(board.render_ascii(demo_state))
