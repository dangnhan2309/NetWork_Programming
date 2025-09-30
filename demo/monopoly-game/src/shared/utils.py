# src/shared/utils.py
import random

def roll_dice():
    """Tung 2 xúc xắc, trả về dict tổng, từng viên, double"""
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    return {"total": d1 + d2, "dice": (d1, d2), "double": d1 == d2}

def format_msg(msg, sender="SYSTEM"):
    """Định dạng tin nhắn gửi client"""
    return {"type": "CHAT", "sender": sender, "message": msg}

def money_format(amount: int):
    """Định dạng số tiền hiển thị"""
    return f"${amount:,}"
