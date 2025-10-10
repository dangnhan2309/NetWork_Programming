 
# src/shared/protocol.py
import json

# Packet types: JOIN, CHAT, EXIT
def encode(packet: dict) -> bytes:
    """
    packet: {'type': 'JOIN'|'CHAT'|'EXIT', 'name': str, 'message': str (optional)}
    returns bytes ending with newline
    """
    return (json.dumps(packet, ensure_ascii=False) + '\n').encode('utf-8')

def decode(data: bytes) -> dict:
    try:
        text = data.decode('utf-8').strip()
        if not text:
            return {}
        return json.loads(text)
    except Exception:
        return {}
# src/shared/protocol.py
import json

# Packet types: JOIN, CHAT, EXIT
def encode(packet: dict) -> bytes:
    """
    packet: {'type': 'JOIN'|'CHAT'|'EXIT', 'name': str, 'message': str (optional)}
    returns bytes ending with newline
    """
    return (json.dumps(packet, ensure_ascii=False) + '\n').encode('utf-8')

def decode(data: bytes) -> dict:
    try:
        text = data.decode('utf-8').strip()
        if not text:
            return {}
        return json.loads(text)
    except Exception:
        return {}
