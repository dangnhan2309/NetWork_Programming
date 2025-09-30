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

HELP_TEXT = """
===========================================================
MONOPOLY CLIENT - DANH SÁCH LỆNH 

📋 LỆNH CƠ BẢN:
  /join <tên>          - Tham gia phòng game
  /help                - Hiển thị hướng dẫn này
  /exit                - Thoát game

🎲 LỆNH GAME:
  /roll                - Gieo xúc xắc và di chuyển
  /buy                 - Mua property đang đứng (nếu được)
  /end_turn            - Kết thúc lượt chơi
  /state               - Xem trạng thái board hiện tại

💬 LỆNH CHAT:
  /say <text>          - Gửi tin nhắn chat
  /chat <text>         - Gửi tin nhắn chat (alias)
  [text thường]        - Gõ text không có / để chat

💰 LỆNH GIAO DỊCH:
  /pay <player> <số tiền> - Trả tiền cho người chơi khác

📝 VÍ DỤ:
  /join Alice
  /roll
  /buy
  /end_turn
  /say Xin chào mọi người!
  /pay Bob 100
===========================================================
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
        return None, HELP_TEXT

    # /join <name>
    if cmd == "/join":
        if len(parts) < 2:
            return None, "❌ Usage: /join <tên>"
        name = " ".join(parts[1:])
        if len(name) > C.MAX_NAME_LEN:
            return None, f"❌ Tên quá dài (tối đa {C.MAX_NAME_LEN} ký tự)"
        return C.m_join(name), None

    # /say <text> | /chat <text>
    if cmd in ("/say", "/chat"):
        if len(parts) < 2:
            return None, "❌ Usage: /say <tin nhắn>"
        text = s[len(cmd):].strip()
        if len(text) > C.MAX_CHAT_LEN:
            return None, f"❌ Tin nhắn quá dài (tối đa {C.MAX_CHAT_LEN} ký tự)"
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
            return None, "❌ Usage: /pay <tên người chơi> <số tiền>"
        to, amt = parts[1], parts[2]
        try:
            value = int(amt)
            if value <= 0:
                return None, "❌ Số tiền phải lớn hơn 0"
            if value > 10000:
                return None, "❌ Số tiền quá lớn (tối đa 10,000)"
        except ValueError:
            return None, "❌ Số tiền phải là số nguyên"
        return C.m_pay(to, value), None

    # /end_turn
    if cmd == "/end_turn":
        return C.m_end_turn(), None

    # /state
    if cmd == "/state":
        return C.m_state_ping(), None

    # /exit
    if cmd == "/exit":
        return C.m_exit(), None

    return None, f"❌ Lệnh không tồn tại: {cmd}. Gõ /help để xem danh sách lệnh"