import json
import random
import string
from datetime import datetime

def generate_id(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def timestamp():
    return datetime.now().strftime("%H:%M:%S")

def encode_packet(data: dict):
    return json.dumps(data).encode('utf-8')

def decode_packet(packet: bytes):
    try:
        return json.loads(packet.decode('utf-8'))
    except Exception:
        return {}
