import json

class Protocol:
    @staticmethod
    def make_packet(cmd: str, data: dict):
        return json.dumps({"action": cmd, "data": data})

    @staticmethod
    def parse_packet(packet: str):
        try:
            return json.loads(packet)
        except json.JSONDecodeError:
            return {"cmd": "ERROR", "data": {"msg": "Invalid packet"}}
