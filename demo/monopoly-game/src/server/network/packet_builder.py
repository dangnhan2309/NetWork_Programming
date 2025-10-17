# server/network/packet_builder.py
import uuid
import datetime
import json


class PacketBuilder:
    """
    Xây dựng packet JSON chuẩn cho hệ thống Monopoly.
    Dùng để gửi/nhận qua multicast hoặc direct socket.
    """

    @staticmethod
    def _base_packet(event_type: str, room_id: str = None, sender_id: str = None, payload: dict = None) -> dict:
        """Khởi tạo gói cơ bản"""
        return {
            "packet_id": str(uuid.uuid4()),  # Mã định danh gói
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": event_type,              # Loại sự kiện (join_room, move, buy_property, ...)
            "room_id": room_id,
            "sender_id": sender_id,
            "payload": payload or {},
        }

    # ------------------------------------------------------------------
    # 👥 ROOM / CONNECTION PACKETS
    # ------------------------------------------------------------------
    @classmethod
    def join_room(cls, room_id: str, player_info: dict):
        return cls._base_packet("join_room", room_id, player_info["id"], {"player": player_info})

    @classmethod
    def leave_room(cls, room_id: str, player_id: str):
        return cls._base_packet("leave_room", room_id, player_id, {"message": f"Player {player_id} left the room."})

    @classmethod
    def start_game(cls, room_id: str, host_id: str):
        return cls._base_packet("start_game", room_id, host_id, {"message": "Game started!"})

    # ------------------------------------------------------------------
    # 🎲 GAME ACTIONS
    # ------------------------------------------------------------------
    @classmethod
    def player_move(cls, room_id: str, player_id: str, new_position: int, dice: tuple):
        return cls._base_packet("player_move", room_id, player_id, {
            "position": new_position,
            "dice": dice
        })

    @classmethod
    def player_buy_property(cls, room_id: str, player_id: str, tile_id: int, price: int, result: dict):
        return cls._base_packet("buy_property", room_id, player_id, {
            "tile_id": tile_id,
            "price": price,
            "result": result
        })

    @classmethod
    def player_pay_tax(cls, room_id: str, player_id: str, amount: int, result: dict):
        return cls._base_packet("pay_tax", room_id, player_id, {
            "amount": amount,
            "result": result
        })

    @classmethod
    def player_transfer(cls, room_id: str, sender_id: str, target_id: str, amount: int, result: dict):
        return cls._base_packet("transfer_money", room_id, sender_id, {
            "target_id": target_id,
            "amount": amount,
            "result": result
        })

    # ------------------------------------------------------------------
    # 🏦 BANK / SYSTEM
    # ------------------------------------------------------------------
    @classmethod
    def update_balance(cls, room_id: str, player_id: str, balance: int):
        return cls._base_packet("update_balance", room_id, player_id, {"balance": balance})

    @classmethod
    def broadcast_state(cls, room_id: str, state: dict):
        return cls._base_packet("broadcast_state", room_id, "server", {"state": state})

    # ------------------------------------------------------------------
    # 🧩 CARD / TILE EVENTS
    # ------------------------------------------------------------------
    @classmethod
    def draw_card(cls, room_id: str, player_id: str, card_type: str, card_data: dict):
        return cls._base_packet("draw_card", room_id, player_id, {
            "card_type": card_type,
            "card_data": card_data
        })

    # ------------------------------------------------------------------
    # ❗ ERROR / SYSTEM MESSAGES
    # ------------------------------------------------------------------
    @classmethod
    def error(cls, room_id: str, player_id: str, message: str):
        return cls._base_packet("error", room_id, player_id, {"message": message})
    @classmethod
    def build(cls, event_type: str, payload: dict, room_id: str = None, sender_id: str = None):
        """
        Tạo packet cho bất kỳ loại event nào (dùng trong Bank, GameManager, v.v.)
        """
        return cls._base_packet(event_type, room_id, sender_id, payload)

    @staticmethod
    def send_to_jail(room_id, player_id, jail_tile_id):
        return {
            "event": "PLAYER_SENT_TO_JAIL",
            "room_id": room_id,
            "payload": {
                "player_id": player_id,
                "tile_id": jail_tile_id,
                "message": "Player rolled three doubles and was sent to Jail!"
            }
        }

    @staticmethod
    def tile_event(room_id, player_id, tile_event):
        """
        Đóng gói kết quả từ tile.on_land()
        """
        return {
            "event": tile_event["event_type"],
            "room_id": room_id,
            "payload": {
                "player_id": player_id,
                "tile": {
                    "id": tile_event["data"]["tile_id"],
                    "name": tile_event["data"]["tile_name"],
                    "type": tile_event["data"]["tile_type"]
                },
                "effect": tile_event["effect"],
                "message": tile_event["message"]
            }
        }
    # ------------------------------------------------------------------
    # 🎲 ROLL DICE / TURN EVENTS
    # ------------------------------------------------------------------
    @classmethod
    def roll_result(cls, room_id: str, player_id: str, dice: tuple, total_steps: int, is_double: bool):
        """
        Gói tin gửi khi người chơi tung xúc xắc (roll dice)
        """
        return cls._base_packet("roll_dice_result", room_id, player_id, {
            "dice": dice,
            "total_steps": total_steps,
            "is_double": is_double
        })

    @classmethod
    def player_move_complete(cls, room_id: str, player_id: str, new_position: int, tile_info: dict, passed_go: bool):
        """
        Gói tin gửi sau khi người chơi di chuyển xong.
        """
        return cls._base_packet("move_complete", room_id, player_id, {
            "position": new_position,
            "tile": tile_info,
            "passed_go": passed_go
        })

    @classmethod
    def next_turn(cls, room_id: str, next_player_id: str):
        """
        Gói tin thông báo chuyển lượt cho client.
        """
        return cls._base_packet("next_turn", room_id, "server", {
            "next_player_id": next_player_id
        })

    # ------------------------------------------------------------------
    # 🏠 PROPERTY / TILE EVENTS (PAY_RENT, BUY_PROPERTY, OWN_PROPERTY)
    # ------------------------------------------------------------------
    @classmethod
    def prompt_buy_property(cls, room_id: str, player_id: str, tile: dict, price: int, message: str):
        """
        Hiển thị prompt hỏi người chơi có muốn mua ô đất không
        """
        return cls._base_packet("prompt_buy_property", room_id, player_id, {
            "tile": tile,
            "price": price,
            "message": message
        })

    @classmethod
    def pay_rent(cls, room_id: str, payer_id: str, owner_id: str, rent: int, message: str):
        """
        Người chơi trả tiền thuê cho chủ sở hữu ô đất
        """
        return cls._base_packet("pay_rent", room_id, payer_id, {
            "owner_id": owner_id,
            "rent": rent,
            "message": message
        })

    @classmethod
    def own_property(cls, room_id: str, player_id: str, tile_id: int, message: str):
        """
        Người chơi dừng ở đất của mình
        """
        return cls._base_packet("own_property", room_id, player_id, {
            "tile_id": tile_id,
            "message": message
        })

    @classmethod
    def info_message(cls, room_id: str, player_id: str, message: str):
        """
        Gửi thông báo chung (không thay đổi trạng thái)
        """
        return cls._base_packet("info_message", room_id, player_id, {
            "message": message
        })

    # ------------------------------------------------------------------
    # 💰 TRANSACTION / BALANCE UPDATES
    # ------------------------------------------------------------------
    @classmethod
    def transfer_rent(cls, room_id: str, payer_id: str, owner_id: str, rent: int, payer_balance: int, owner_balance: int):
        """
        Gửi khi hoàn tất giao dịch thuê (payer trả, owner nhận)
        """
        return cls._base_packet("transfer_rent", room_id, "server", {
            "payer_id": payer_id,
            "owner_id": owner_id,
            "rent": rent,
            "payer_balance": payer_balance,
            "owner_balance": owner_balance
        })

    @classmethod
    def pass_go_bonus(cls, room_id: str, player_id: str, amount: int, new_balance: int):
        """
        Khi người chơi đi qua ô GO và nhận $200
        """
        return cls._base_packet("pass_go_bonus", room_id, player_id, {
            "amount": amount,
            "new_balance": new_balance,
            "message": f"Player {player_id} passed GO and received ${amount}!"
        })
