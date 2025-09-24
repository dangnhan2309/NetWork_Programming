"""
Parse lệnh người chơi từ console -> message JSON (dict) gửi server.
Dùng chung với protocol NDJSON (encode/decode đã có ở src/shared/protocol.py).

Cú pháp (client):
  /join <name>
  /say <text>        (alias /chat)
  /roll
  /buy
  /pay <player> <amount>
  /end
  /state             (xin trạng thái board)
  /exit
  /help
"""

from typing import Optional, Tuple
from src.shared import constants as C

HELP = """Commands:
/join <name>          - join phòng
/say <text>           - chat (alias: /chat)
/roll                 - gieo xúc xắc
/buy                  - mua ô đang đứng (nếu được)
/pay <player> <amt>   - trả tiền cho người chơi
/end                  - kết thúc lượt
/state                - xin trạng thái board
/exit                 - thoát
/help                 - hướng dẫn
"""

def parse_cmd(line: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Trả về: (message_dict | None, error_string | None)
    - Nếu là lệnh hợp lệ -> (msg, None)
    - Nếu là chat thường (không dấu /) -> tự động chuyển thành CHAT
    - Nếu lỗi cú pháp -> (None, "...error...")
    """
    s = (line or "").strip()
    if not s:
        return None, None

    # Chat không có dấu / -> gửi CHAT
    if not s.startswith("/"):
        return C.m_chat(s), None

    parts = s.split()
    cmd = parts[0].lower()

    # /help
    if cmd == "/help":
        return None, HELP

    # /join <name>
    if cmd == "/join":
        if len(parts) < 2:
            return None, "Usage: /join <name>"
        name = " ".join(parts[1:])
        return C.m_join(name), None

    # /say <text> | /chat <text>
    if cmd in ("/say", "/chat"):
        if len(parts) < 2:
            return None, "Usage: /say <text>"
        text = s[len(cmd):].strip()
        return C.m_chat(text), None

    # /roll
    if cmd == "/roll":
        return C.m_roll(), None

    # /buy
    if cmd == "/buy":
        return C.m_buy(), None

    # /pay <player> <amt>
    if cmd == "/pay":
        if len(parts) != 3:
            return None, "Usage: /pay <player> <amount>"
        to, amt = parts[1], parts[2]
        try:
            value = int(amt)
        except ValueError:
            return None, "Amount must be integer"
        return C.m_pay(to, value), None

    # /end
    if cmd == "/end":
        return C.m_end_turn(), None

    # /state
    if cmd == "/state":
        return C.m_state_ping(), None

    # /exit
    if cmd == "/exit":
        return C.m_exit(), None

    return None, f"Unknown command: {cmd}. Type /help"
