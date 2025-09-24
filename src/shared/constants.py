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

# Server side messages tham khảo
def m_info(msg: str) -> dict:
    return {K_TYPE: INFO, K_MSG: msg}

def m_error(reason: str) -> dict:
    return {K_TYPE: ERROR, K_REASON: reason}
