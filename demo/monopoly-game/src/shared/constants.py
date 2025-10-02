"""
Hằng số & giao thức dùng chung cho client/server (GĐ3 – Multiplayer)

Wire format: NDJSON (one JSON object per line)
  {"type": "JOIN", "name": "Tai"}
  {"type": "CHAT", "msg": "hello"}
  {"type": "ROLL"}
  {"type": "BUY"}
  {"type": "PAY", "to": "PlayerA", "amount": 50}
  {"type": "END_TURN"}
Mọi message phải có trường "type".
"""

# ==== Message Types (string literal để dễ serialize JSON) ====
JOIN        = "JOIN"
CHAT        = "CHAT"
EXIT        = "EXIT"
ROLL        = "ROLL"
BUY         = "BUY"
PAY         = "PAY"
END_TURN    = "END_TURN"
STATE_PING  = "STATE_PING"   # client -> server xin state
STATE_PUSH  = "STATE_PUSH"   # server -> client broadcast state
ERROR       = "ERR"
INFO        = "INFO"

# ==== Các key phổ biến trong payload ====
K_TYPE      = "type"
K_NAME      = "name"
K_MSG       = "msg"
K_TO        = "to"
K_AMOUNT    = "amount"
K_STATE     = "state"        # trạng thái board/gamefull
K_REASON    = "reason"

# ==== Game limits / timeouts ====
MAX_PLAYERS         = 4
TURN_TIMEOUT_SEC    = 60       # quá 60s auto END_TURN
HEARTBEAT_SEC       = 20       # ping/pong nếu dùng websockets
MAX_CHAT_LEN        = 500
MAX_NAME_LEN        = 20
CONNECTION_TIMEOUT  = 30       # timeout kết nối client
GAME_START_DELAY    = 5        # delay trước khi bắt đầu game
BOARD_SIZE          = 40       # số ô trên bàn cờ monopoly
STARTING_MONEY      = 1500     # tiền ban đầu mỗi player

# ==== Helper: tạo message chuẩn ====
def m_join(name: str) -> dict:
    return {K_TYPE: JOIN, K_NAME: name[:MAX_NAME_LEN]}

def m_chat(text: str) -> dict:
    return {K_TYPE: CHAT, K_MSG: text[:MAX_CHAT_LEN]}

def m_exit() -> dict:
    return {K_TYPE: EXIT}

def m_roll() -> dict:
    return {K_TYPE: ROLL}

def m_buy() -> dict:
    return {K_TYPE: BUY}

def m_pay(to: str, amount: int) -> dict:
    return {K_TYPE: PAY, K_TO: to, K_AMOUNT: int(amount)}

def m_end_turn() -> dict:
    return {K_TYPE: END_TURN}

def m_state_ping() -> dict:
    return {K_TYPE: STATE_PING}

def m_state_push(state: dict) -> dict:
    return {K_TYPE: STATE_PUSH, K_STATE: state}

# Server side messages tham khảo
def m_info(msg: str) -> dict:
    return {K_TYPE: INFO, K_MSG: msg}

def m_error(reason: str) -> dict:
    return {K_TYPE: ERROR, K_REASON: reason}

# ==== Game State Keys ====
K_PLAYERS       = "players"
K_CURRENT_TURN  = "current_turn"
K_BOARD         = "board"
K_GAME_STATE    = "game_state"
K_PLAYER_POS    = "position"
K_PLAYER_MONEY  = "balance"
K_PLAYER_PROPERTIES = "properties"
K_TILE_OWNER    = "owner"
K_TILE_TYPE     = "type"
K_TILE_NAME     = "name"
K_TILE_PRICE    = "price"
K_TILE_RENT     = "rent"

# ==== Game States ====
GAME_WAITING    = "waiting"    # chờ đủ player
GAME_PLAYING    = "playing"    # đang chơi
GAME_ENDED      = "ended"      # kết thúc

# Define Community Chest cards
community_chest_cards = [
    "Advance to Go (Collect $200)",
    "Bank error in your favor – Collect $200",
    "Doctor’s fees – Pay $50",
    "From sale of stock you get $50",
    "Get Out of Jail Free",
    "Go to Jail – Go directly to jail – Do not pass Go – Do not collect $200",
    "Grand Opera Night – Collect $50 from every player for opening night seats",
    "Holiday Fund matures – Receive $100",
    "Income tax refund – Collect $20",
    "It is your birthday – Collect $10 from every player",
    "Life insurance matures – Collect $100",
    "Hospital Fees – Pay $50",
    "School fees – Pay $50",
    "Receive $25 consultancy fee",
    "You are assessed for street repairs – $40 per house, $115 per hotel",
    "You have won second prize in a beauty contest – Collect $10"
]
chance_cards = [
    "Advance to Go (Collect $200)",
    "Advance to Illinois Ave. If you pass Go, collect $200",
    "Advance to St. Charles Place. If you pass Go, collect $200",
    "Advance token to nearest Utility. If unowned, buy it. If owned, pay rent.",
    "Advance token to nearest Railroad. Pay owner double rent. If unowned, you may buy.",
    "Bank pays you dividend of $50",
    "Get Out of Jail Free",
    "Go Back 3 Spaces",
    "Go to Jail – Go directly to jail – Do not pass Go – Do not collect $200",
    "Make general repairs on all your property: For each house pay $25, For each hotel $100",
    "Pay poor tax of $15",
    "Take a trip to Reading Railroad. If you pass Go, collect $200",
    "Take a walk on the Boardwalk. Advance token to Boardwalk",
    "You have been elected Chairman of the Board – Pay each player $50",
    "Your building loan matures – Collect $150",
    "You have won a crossword competition – Collect $100"
]


# Function to draw card
import random

def draw_card(deck, keep=False):
    """
    Rút ngẫu nhiên một lá bài từ bộ bài.
    Nếu keep=True, lá bài sẽ bị xóa khỏi bộ bài.
    Nếu False, lá bài sẽ được trả về cuối bộ bài.
    """
    if not deck:
        return None  # Trả về None nếu bộ bài rỗng

    # Sử dụng random.sample() để chọn ngẫu nhiên một lá bài.
    # [0] được thêm vào để trích xuất phần tử duy nhất từ danh sách kết quả.
    card = random.sample(deck, 1)[0]

    if keep:
        deck.remove(card)
    else:
        # Xóa lá bài đã rút và thêm nó vào cuối danh sách.
        deck.remove(card)
        deck.append(card)

    return card


