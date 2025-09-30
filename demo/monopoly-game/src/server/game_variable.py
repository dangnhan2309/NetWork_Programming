import collections
Assets = {
    # Right edge (bottom -> top)
    "Mediterranean Avenue": {
        "name": "Mediterranean Avenue",
        "owner": "None",
        "cost": 60,
        "position": 1,
        "color_group": "Brown",
        "rent": {
            "no_houses": 2,
            "1_house": 10,
            "2_houses": 30,
            "3_houses": 90,
            "4_houses": 160,
            "hotel": 250
        },
        "house_cost": 50,
        "num_houses": 0,
        "mortgage_value": 30
    },
    "Community Chest 1": [],
    "Baltic Ave": [],
    "Income Tax": [],
    "Reading Railroad": [],
    "Oriental Ave": [],
    "Chance 1": [],
    "Vermont Ave": [],
    "Connecticut Ave": [],

    # Top edge (right -> left)
    "Jail / Just Visiting": [],
    "St. Charles Place": [],
    "Electric Company": [],
    "States Ave": [],
    "Virginia Ave": [],
    "Pennsylvania Railroad": [],
    "St. James Place": [],
    "Community Chest 2": [],
    "Tennessee Ave": [],
    "New York Ave": [],

    # Left edge (top -> bottom)
    "Free Parking": [],
    "Kentucky Ave": [],
    "Chance 2": [],
    "Indiana Ave": [],
    "Illinois Ave": [],
    "B&O Railroad": [],
    "Atlantic Ave": [],
    "Ventnor Ave": [],
    "Water Works": [],
    "Marvin Gardens": [],

    # Bottom edge (left -> right)
    "Go To Jail": [],
    "Pacific Ave": [],
    "North Carolina Ave": [],
    "Community Chest": [],
    "Pennsylvania Ave": [],
    "Short Line Railroad": [],
    "Chance": [],
    "Park Place": [],
    "Luxury Tax": [],
    "Boardwalk": []
}
Tracker2 = {
    # Cạnh phải (từ dưới lên trên)
    "Điểm Xuất Phát": [],
    "Phố Tạ Hiện": [],
    "Khí Vận 1": [],
    "Hồ Gươm": [],
    "Thuế Thu Nhập": [],
    "Ga Sài Gòn": [],
    "Chợ Bến Thành": [],
    "Cơ Hội 1": [],
    "Nhà Thờ Đức Bà": [],
    "Dinh Độc Lập": [],

    # Cạnh trên (từ phải sang trái)
    "Vào Tù / Thăm Tù": [],
    "Khu Phố Cổ Hội An": [],
    "Công Ty Điện Lực": [],
    "Cầu Rồng Đà Nẵng": [],
    "Phố Đi Bộ Nguyễn Huệ": [],
    "Ga Hà Nội": [],
    "Landmark 81": [],
    "Khí Vận 2": [],
    "Nhà Hát Lớn Hà Nội": [],
    "Phú Quốc": [],

    # Cạnh trái (từ trên xuống dưới)
    "Vào Bãi Đỗ Xe Tự Do": [],
    "Vịnh Hạ Long": [],
    "Cơ Hội 2": [],
    "Sa Pa": [],
    "Phố Tây Bùi Viện": [],
    "Ga Đà Nẵng": [],
    "Phố Đi Bộ Bùi Thị Xuân": [],
    "Phố Đèn Lồng Lương Nhữ Học": [],
    "Công Ty Nước Sạch": [],
    "Phố Cổ Đồng Văn": [],

    # Cạnh dưới (từ trái sang phải)
    "Vào Tù": [],
    "Sơn Đoòng": [],
    "Ruộng Bậc Thang Mù Cang Chải": [],
    "Khí Vận": [],
    "Tháp Rùa": [],
    "Ga Hải Phòng": [],
    "Cơ Hội": [],
    "Lăng Bác": [],
    "Thuế Tiêu Dùng": [],
    "Bờ Hồ" : []
}
# src/ascii_board/tiles.py
TILES = [ # bien thanh class
    # 0..9 (right edge, bottom -> top)
    "GO",
    "Mediterranean Ave",
    "Community Chest",
    "Baltic Ave",
    "Income Tax",
    "Reading Railroad",
    "Oriental Ave",
    "Chance",
    "Vermont Ave",
    "Connecticut Ave",

    # 10..19 (top edge, right -> left)
    "Jail / Just Visiting",
    "St. Charles Place",
    "Electric Company",
    "States Ave",
    "Virginia Ave",
    "Pennsylvania Railroad",
    "St. James Place",
    "Community Chest",
    "Tennessee Ave",
    "New York Ave",

    # 20..29 (left edge, top -> bottom)
    "Free Parking",
    "Kentucky Ave",
    "Chance",
    "Indiana Ave",
    "Illinois Ave",
    "B&O Railroad",
    "Atlantic Ave",
    "Ventnor Ave",
    "Water Works",
    "Marvin Gardens",

    # 30..39 (bottom edge, left -> right)
    "Go To Jail",
    "Pacific Ave",
    "North Carolina Ave",
    "Community Chest",
    "Pennsylvania Ave",
    "Short Line Railroad",
    "Chance",
    "Park Place",
    "Luxury Tax",
    "Boardwalk"
]
# Note: TILES[0] = "GO", TILES[10] = "Jail", TILES[20] = "Free Parking", TILES[30] = "Go To Jail"


class GameVariable:
    def __init__(self):
        # The Bank starts with a large amount of money for transactions.
        self.bank_funds = float('inf')  # Or a large number like 20,580
        self.tiles = TILES
        self.assets = Assets
        # A list to hold all unowned properties by their position on the board
        self.buyable_lands = list(range(40))  # Start with all 40 tiles

        # A list to store positions of non-buyable tiles (e.g., GO, Jail, Tax)
        self.non_buyable_lands = [0, 2, 4, 7, 10, 17, 20, 22, 30, 33, 36, 38]

        # Inventory of houses and hotels
        self.houses_in_bank = 4
        self.hotels_in_bank = 4

        # Dictionary to store the owner of each buyable property
        self.player_num = 4
        # Dictionary to store the number of houses/hotels on each property
        self.property_usage = collections.defaultdict(int)  # {position: num_of_houses}

        # Starting position of all players
        self.start_at = 0