"""
Demo: Hiển thị bàn cờ Monopoly bằng ASCII
-----------------------------------------

Mục đích:
- Kiểm thử class Board và hàm render_ascii().
- Đảm bảo mapping 0..39 đi NGƯỢC kim đồng hồ quanh viền 11x11:
    0  = GO (góc dưới-phải)
    10 = Jail / Just Visiting (góc dưới-trái)
    20 = Free Parking (góc trên-trái)
    30 = Go To Jail (góc trên-phải)

Nội dung demo_state:
- players: 4 người chơi A, B, C, D với vị trí mẫu
    A: pos=0   → GO (góc dưới-phải)
    B: pos=10  → Jail (góc dưới-trái)
    C: pos=24  → Illinois Ave (cạnh trên, giữa)
    D: pos=39  → Boardwalk (ngay trước GO, cạnh phải)
- ownership: một vài ô mẫu được gán chủ sở hữu (A/B/C/D)
- buildings: ô 1 có 2 nhà, ô 39 có khách sạn

Cách chạy:
    python -m src.ascii_board.demo_board

Kết quả mong đợi:
- Bàn cờ ASCII 11x11 với 40 ô viền ngoài.
- Góc và cạnh hiển thị đúng thứ tự 0..39.
- Tên ô, chủ sở hữu, số nhà/khách sạn, và vị trí người chơi được in ra.
"""


# Import class Board từ file board.py
from .board import Board

# Trạng thái demo để test hiển thị board
demo_state = {
    # Danh sách người chơi với vị trí hiện tại
    # 0 = GO (góc dưới-phải)
    # 10 = Jail / Just Visiting (góc dưới-trái)
    # 20 = Free Parking (góc trên-trái)
    # 30 = Go To Jail (góc trên-phải)
    "players": [
        {"nick": "A", "pos": 0},     # A đứng ở GO (góc dưới-phải)
        {"nick": "B", "pos": 10},    # B đứng ở Jail (góc dưới-trái)
        {"nick": "C", "pos": 24},    # C đứng ở Illinois Ave (cạnh trên, giữa)
        {"nick": "D", "pos": 39},    # D đứng ở Boardwalk (ngay trước GO, cạnh phải)
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
