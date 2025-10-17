"""
Phân tích lệnh từ người chơi → trả về message JSON
"""
import json

COMMANDS = [
    "/help", "/chat", "/roll", "/buy", "/end", "/exit", "/players",
    "/start", "/test", "/trade", "/build", "/mortgage", "/unmortgage",
    "/usecard", "/state"
]

def parse_cmd(text: str):
    text = text.strip()
    if not text:
        return None, None

    # === System commands ===
    if text == "/help":
        return {
            "type": "system",
            "command": "help",
            "info": """
📜 Danh sách lệnh:
 /chat <msg>        → Gửi tin nhắn
 /roll              → Đổ xúc xắc
 /buy               → Mua tài sản
 /end               → Kết thúc lượt
 /trade <player> <offer> <request> → Giao dịch
 /build <property>  → Xây nhà/khách sạn
 /mortgage <property>   → Cầm cố tài sản
 /unmortgage <property> → Giải chấp
 /usecard <name>    → Dùng thẻ (VD: Get Out of Jail Free)
 /players           → Danh sách người chơi
 /state             → Xem trạng thái bàn
 /start             → Bắt đầu ván
 /exit              → Thoát game
 /test              → Chế độ thử nghiệm
            """
        }, None

    elif text == "/exit":
        return {"type": "system", "command": "exit"}, None

    elif text == "/players":
        return {"type": "system", "command": "players"}, None

    elif text == "/start":
        return {"type": "system", "command": "start"}, None

    elif text == "/state":
        return {"type": "system", "command": "state"}, None

    elif text == "/test":
        return {"type": "debug", "command": "test"}, None

    # === Chat ===
    elif text.startswith("/chat"):
        msg = text[5:].strip()
        if not msg:
            return None, "⚠️ Lệnh chat cần nội dung: /chat <message>"
        return {"type": "chat", "message": msg}, None

    # === Game Actions ===
    elif text.startswith("/roll"):
        return {"type": "action", "action": "roll"}, None

    elif text.startswith("/buy"):
        return {"type": "action", "action": "buy"}, None

    elif text.startswith("/end"):
        return {"type": "action", "action": "end_turn"}, None

    elif text.startswith("/trade"):
        parts = text.split()
        if len(parts) < 4:
            return None, "⚠️ Cú pháp: /trade <player> <offer> <request>"
        player, offer, request = parts[1], parts[2], parts[3]
        return {"type": "action", "action": "trade", "target": player, "offer": offer, "request": request}, None

    elif text.startswith("/build"):
        parts = text.split()
        if len(parts) < 2:
            return None, "⚠️ Cú pháp: /build <property>"
        return {"type": "action", "action": "build", "property": parts[1]}, None

    elif text.startswith("/mortgage"):
        parts = text.split()
        if len(parts) < 2:
            return None, "⚠️ Cú pháp: /mortgage <property>"
        return {"type": "action", "action": "mortgage", "property": parts[1]}, None

    elif text.startswith("/unmortgage"):
        parts = text.split()
        if len(parts) < 2:
            return None, "⚠️ Cú pháp: /unmortgage <property>"
        return {"type": "action", "action": "unmortgage", "property": parts[1]}, None

    elif text.startswith("/usecard"):
        parts = text.split()
        if len(parts) < 2:
            return None, "⚠️ Cú pháp: /usecard <card_name>"
        return {"type": "action", "action": "use_card", "card_name": parts[1]}, None

    # === Invalid command ===
    else:
        return None, f"⚠️ Lệnh không hợp lệ: {text}. Gõ /help để xem danh sách lệnh."

