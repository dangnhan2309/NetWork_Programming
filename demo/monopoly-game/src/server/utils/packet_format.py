# src/utils/packet_format.py
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any


class PacketFormat:
    """
    Cấu trúc packet chuẩn cho Monopoly Multiplayer (UDP Multicast)
    ---------------------------------------------------------------
    header: định danh, loại, thời gian, phiên bản
    meta: seq, ack, reliability, hop_count
    command: lệnh game
    payload: dữ liệu trả về / thông báo
    """

    VERSION = "1.0"

    @staticmethod
    def generate_timestamp() -> str:
        """ISO 8601 UTC format with Z"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def create_packet(
        packet_type: str,
        room_id: str,
        sender: str,
        target: str,
        action: str,
        args: Dict[str, Any] = None,
        payload: Dict[str, Any] = None,
        seq_id: int = None,
        ack: bool = False,
        reliable: bool = True,
        hop_count: int = 1
    ) -> dict:
        """Tạo packet chuẩn cho multicast communication."""
        packet_id = f"{sender}-{uuid.uuid4()}"
        timestamp = PacketFormat.generate_timestamp()
        packet = {
            "header": {
                "packet_id": packet_id,
                "room_id": room_id,
                "sender": sender,
                "target": target,
                "type": packet_type,
                "timestamp": timestamp,
                "version": PacketFormat.VERSION
            },
            "meta": {
                "seq_id": seq_id or int(time.time() * 1000),
                "ack": ack,
                "reliable": reliable,
                "hop_count": hop_count
            },
            "command": {
                "action": action,
                "args": args or {}
            },
            "payload": payload or {"status": "OK", "message": ""}
        }
        return packet

    @staticmethod
    def encode_packet(packet: dict) -> bytes:
        """Encode packet sang bytes (JSON)."""
        try:
            return json.dumps(packet, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            raise ValueError(f"Encoding packet failed: {e}")

    @staticmethod
    def encode_for_tcp(packet: dict) -> bytes:
        """
        Encode packet để gửi qua TCP - thêm newline '\n' làm delimiter.
        Client/server TCP của bạn nên đọc theo dòng hoặc phân tích delimiter.
        """
        try:
            return (json.dumps(packet, ensure_ascii=False) + "\n").encode("utf-8")
        except Exception as e:
            raise ValueError(f"Encoding packet for TCP failed: {e}")

    @staticmethod
    def decode_packet(raw: bytes) -> dict:
        """Decode packet từ bytes về dict."""
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Decoding packet failed: {e}")

    @staticmethod
    def is_valid(packet: dict) -> bool:
        """Kiểm tra cấu trúc packet hợp lệ."""
        required_sections = ["header", "meta", "command", "payload"]
        return all(section in packet for section in required_sections)

    @staticmethod
    def pretty_print(packet: dict):
        """In gói tin dễ đọc."""
        print(json.dumps(packet, indent=4, ensure_ascii=False))
