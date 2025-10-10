"""
Phân tích lệnh từ người chơi → trả về message JSON
"""
import json

def parse_cmd(text: str):
 
    text = text.strip()
    if not text:
        return None, None

    # Lệnh chat
    if text.startswith("/chat"):
        msg = text[5:].strip()
        return {"type": "chat", "message": msg}, None

    # Lệnh roll
    elif text.startswith("/roll"):
        return {"type": "action", "action": "roll"}, None

    # Lệnh buy
    elif text.startswith("/buy"):
        return {"type": "action", "action": "buy"}, None

    # Lệnh end turn
    elif text.startswith("/end"):
        return {"type": "action", "action": "end_turn"}, None

    # Exit
    elif text == "/exit":
        return {"type": "exit"}, None

    else:
        return None, f"⚠️ Lệnh không hợp lệ: {text}. Thử /chat, /roll, /buy, /end"
