# """
# board.py
# ---------------------------------
# Lớp Board chịu trách nhiệm:
# - Quản lý danh sách ô (Tile)
# - Cập nhật vị trí người chơi
# - Xử lý di chuyển và gọi hiệu ứng ô
# - Trả về trạng thái bàn cờ (dùng cho GameManager hoặc client UI)
# """
#
# from typing import List, Dict, Optional, Any
# import random
# import json
# from pathlib import Path
# from .player import Player
#
# # Import các loại Tile từ thư mục tiles
# from .tiles.base_tile import BaseTile
# from .tiles import *
# from .properties import *
# from .Bank import Bank
# from ..utils.load_data import load_property_data_from_file
# BOARD_JSON_PATH =r"demo/monopoly-game/src/server/game/board_config.json"
# from .player import Player
#
# class Board:
#     """Quản lý logic bàn cờ Monopoly"""
#
#
#     def __init__(self):
#         self.tiles: List[BaseTile] = self._create_board()
#         # Có thể thêm các biến global như pool tiền thuế, nhà tù, v.v.
#         self.free_parking_pool = 0
#         self.bank = Bank()
#         self.board_path = BOARD_JSON_PATH
#         self.players = []
#
#     # ======================================================
#     # 1️⃣ KHỞI TẠO CÁC Ô TRÊN BÀN CỜ
#     # ======================================================
#     def _create_board(self) -> List[BaseTile]:
#         """
#         Tải cấu hình bàn cờ từ file JSON và tạo danh sách các ô trên bàn cờ.
#         Đường dẫn giả định: 'D:/NetWork_Programming/demo/monopoly-game/src/server/game/board_config.json'
#         """
#         # CHÚ Ý: Đường dẫn này cần được điều chỉnh cho môi trường thực tế của bạn.
#         # Sử dụng Path để đảm bảo tương thích trên các hệ điều hành.
#         # Giả sử file JSON nằm trong thư mục ngang cấp với thư mục 'game' hoặc một vị trí cố định khác.
#         # Trong ví dụ này, tôi dùng đường dẫn tuyệt đối bạn cung cấp.
#
#         config_data = load_property_data_from_file(BOARD_JSON_PATH)
#
#         tiles: List[BaseTile] = []
#
#         # Duyệt qua danh sách các ô (tiles) trong JSON
#         for tile_data in config_data.get("tiles", []):
#             tile_id = tile_data["id"]
#             name = tile_data["name"]
#             tile_type = tile_data["type"]
#             position = tile_id
#             color = tile_data["color"]# Vị trí thường bằng ID trong Monopoly
#
#             # Dựa vào loại ô cờ ('type') để tạo đối tượng Tile thích hợp
#             if tile_type == "property":
#                 if color =="utility":
#                     tile = UtilityTile(
#                         tile_id=tile_id,
#                         name=name,
#                         position=position,
#                         properties_obj=UtilityProperty(tile_data["property_info"]),
#
#
#                     )
#                 elif color =="railroad":
#                     tile = RailroadTile(
#                         tile_id=tile_id,
#                         name=name,
#                         position=position,
#                         properties_obj=RailroadProperty(tile_data["property_info"]),
#                     )
#
#                 else:
#                     # Tạo đối tượng PropertyTile
#                     tile = PropertyTile(
#                         tile_id=tile_id,
#                         name=name,
#                         position=position,
#                         properties_obj =ColorGroupProperty(tile_data["property_info"]),
#                         colour=tile_data["color"]  # Lấy thuộc tính color từ JSON
#                     )
#
#             elif tile_type in ("go", "jail", "parking", "goto_jail"):
#                 # Các ô đơn giản không có logic mua/bán
#                 tile = BaseTile(tile_id, name, position, tile_type)
#
#             elif tile_type == "chance":
#                 tile = ChanceTile(tile_id = tile_id, name = name,deck="chance" ,position =position)
#             elif tile_type == "community":
#                 tile = CommunityTile(tile_id = tile_id, name = name,deck="community" ,position =position)
#
#             elif tile_type == "tax":
#                 # Giả định bạn có class TaxTile
#                 # tile = TaxTile(tile_id, name, position, amount=tile_data["amount"])
#                 tile = TaxTile(tile_id, name, position, tile_type)  # Dùng BaseTile tạm
#
#             else:
#                 # Xử lý các loại ô không xác định
#                 tile = BaseTile(tile_id, name, position, tile_type)
#
#             tiles.append(tile)
#
#         return tiles
#     # ======================================================
#     # 2️⃣ DI CHUYỂN NGƯỜI CHƠI
#     # ======================================================
#     def move_player(self, player: 'Player', steps: int, all_players: List['Player']) -> Dict[str, Any]:
#         old_pos = player.position
#         board_length = len(self.tiles)  # Giả sử 40
#
#         # Tính toán vị trí mới
#         new_pos = (old_pos + steps) % board_length
#
#         # Kiểm tra xem người chơi có vượt qua ô GO (Vị trí 0) hay không
#         # Điều này xảy ra nếu old_pos + steps >= board_length
#         passed_go = (old_pos + steps) >= board_length
#
#         # Cập nhật vị trí
#         player.position = new_pos
#
#         return {
#             "tile_id": new_pos,
#             "old_position": old_pos,
#             "new_position": new_pos,
#             "passed_go": passed_go,
#             "teleported": False  # Di chuyển xúc xắc là False
#         }
#
#     # ======================================================
#     # 3️⃣ LẤY THÔNG TIN Ô VÀ TRẠNG THÁI BÀN
#     # ======================================================
#     def get_tile(self, tile_id: int) -> Optional[BaseTile]:
#         """Lấy ô theo ID"""
#         return next((t for t in self.tiles if t.tile_id == tile_id), None)
#
#     def get_board_state(self) -> Dict:
#         """
#         Trả về toàn bộ trạng thái bàn cờ, bao gồm thông tin chi tiết
#         về từng ô đất và trạng thái sở hữu (truy vấn từ Bank).
#         """
#         board_state = {
#             "tiles": [],
#             "bank_data": {
#                 "cash_pool": self.bank.cash_pool,
#                 "free_parking_pool": self.bank.free_parking_pool,
#                 # Thêm thông tin về kho vật chất nếu Bank quản lý Houses/Hotels
#                 # "houses_available": self.bank.houses_available,
#                 # "hotels_available": self.bank.hotels_available
#             }
#         }
#
#         # Duyệt qua từng ô đất và gọi phương thức to_dict()
#         for tile in self.tiles:
#             tile_data = {}
#
#             # Đối với PropertyTile, cần truyền Bank để xác định chủ sở hữu.
#             # Lưu ý: Các loại Tile khác cần được kiểm tra để tránh lỗi AttributeError
#             if isinstance(tile, PropertyTile):
#                 # Giả định rằng PropertyTile đã được điều chỉnh để nhận bank_service
#                 tile_data = tile.to_dict()
#
#             elif isinstance(tile, UtilityTile):
#                 tile_data = tile.to_dict()
#
#             elif isinstance(tile, RailroadTile):
#                 tile_data = tile.to_dict()
#
#             else:
#                 # Đối với BaseTile hoặc các loại Tile khác không có logic sở hữu
#                 tile_data = tile.to_dict()
#
#             board_state["tiles"].append(tile_data)
#
#         return board_state
#     def update_property(self):
#         pass
#         """"""
#
#     def get_property_by_property_id(self, property_id: int):
#         """
#         Tìm và trả về đối tượng PropertyTile, UtilityTile, hoặc RailroadTile
#         dựa trên ID của ô đất.
#         """
#         # Duyệt qua danh sách các ô (tiles) trên Board
#         for tile in self.tiles:
#             # 1. Kiểm tra ID có khớp không
#             if tile.tile_id == property_id:
#
#                 # 2. Kiểm tra xem ô đó có phải là loại tài sản có thể mua (property) hay không
#                 # Ta kiểm tra dựa trên thuộc tính 'properties_obj' hoặc 'tile_type'
#                 if tile.tile_type in ["property", "utility", "railroad"]:
#                     return tile
#                 else:
#                     # Nếu tìm thấy ID nhưng đó không phải là một tài sản có thể mua (ví dụ: GO, Jail, Tax)
#                     return None
#
#                     # Trả về None nếu không tìm thấy ô đất nào có ID tương ứng
#         return None
#
#     def get_player_by_id(self, id_player: int) -> Optional['Player']:
#         """
#         Tìm và trả về đối tượng Player dựa trên ID của người chơi.
#         """
#         # Duyệt qua danh sách self.players để tìm người chơi có ID tương ứng
#         for player in self.players:
#             if player.id == id_player:
#                 return player
#
#         # Trả về None nếu không tìm thấy người chơi nào
#         return None
#
#     def get_jail_tile(self):
#         for tile in self.tiles:
#             if tile.tile_type == "jail":
#                 return tile
#         return None
#
#     def send_player_to_jail(self, player : Player):
#         """Đưa người chơi vào Jail (ô có type='jail')"""
#         jail_tile = next((t for t in self.tiles if t.tile_type == "jail"), None)
#         if jail_tile:
#             player.position = jail_tile.tile_id
#             player.in_jail = True
#             return {"event": "jail", "message": f"{player.name} was sent to jail!"}
#         return {"event": "error", "message": "Jail not found on board!"}
#
#     def reset_owner(self, player_id: str):
#         self.bank.reset_property_owner(int(player_id))
#
#         # Trả về thông báo hoặc trạng thái để xử lý log/UI
#         return {"event": "owner_reset", "message": f"All properties owned by Player ID {player_id} are now unowned."}
# # ======================================================
#     # 5️⃣ SERIALIZATION
#     # ======================================================
#     def serialize_dict(self) -> Dict:
#         """
#         Serialize toàn bộ trạng thái của đối tượng Board thành một dictionary.
#         Phương thức này tương đương với get_board_state().
#         """
#         return self.get_board_state()
#
#     def serialize_json(self) -> str:
#         """
#         Chuyển đổi trạng thái Board đã serialize (dictionary) thành chuỗi JSON.
#         """
#         # Sử dụng serialize_dict() để lấy dữ liệu trước khi chuyển thành JSON
#         return json.dumps(self.serialize_dict(), indent=4)


"""
board.py — phiên bản chuẩn với logic Monopoly
---------------------------------------------
Nhiệm vụ:
- Quản lý danh sách Tile
- Xử lý di chuyển người chơi
- Kích hoạt logic on_land() của Tile
- Gọi đến Bank khi cần thực hiện giao dịch
"""

from typing import List, Dict, Optional, Any
import random, json
from pathlib import Path

from .player import Player
from .Bank import Bank
from .tiles.base_tile import BaseTile
from .tiles.chance_tile import ChanceTile
from .tiles.communityChestTile import CommunityTile
from .tiles.property_tile import PropertyTile
from .tiles.railroad_tile import RailroadTile
from .tiles.utility_tile import UtilityTile
from .tiles.tax_tile import TaxTile
from .tiles.jail_tile import JailTile
from .tiles.free_parking_title import FreeParkingTile
from .tiles.goto_jail_tile import GoToJailTile
from ..utils.load_data import load_property_data_from_file

BOARD_JSON_PATH = r"demo/monopoly-game/src/server/game/board_config.json"


class Board:
    def __init__(self):
        self.tiles: List[BaseTile] = self._create_board()
        self.bank = Bank()
        self.players: List[Player] = []
        self.board_path = BOARD_JSON_PATH

    # ======================================================
    # 1️⃣ KHỞI TẠO BOARD
    # ======================================================
    def _create_board(self) -> List[BaseTile]:
        config = load_property_data_from_file(BOARD_JSON_PATH)
        tiles: List[BaseTile] = []

        for tile_data in config.get("tiles", []):
            tile_type = tile_data["type"]
            tile_id = tile_data["id"]
            name = tile_data["name"]
            color = tile_data.get("color", None)
            position = tile_id

            if tile_type == "property":
                if color == "utility":
                    tile = UtilityTile(tile_id, name, position, tile_data["property_info"])
                elif color == "railroad":
                    tile = RailroadTile(tile_id, name, position, tile_data["property_info"])
                else:
                    tile = PropertyTile(tile_id, name, position, tile_data["property_info"], color)

            elif tile_type == "chance":
                tile = ChanceTile(tile_id, name, position, deck="chance")

            elif tile_type == "community":
                tile = CommunityTile(tile_id, name, position, deck="community")

            elif tile_type == "tax":
                tile = TaxTile(tile_id, name, position, amount=tile_data["amount"])

            elif tile_type == "jail":
                tile = JailTile(tile_id, name, position)

            elif tile_type == "parking":
                tile = FreeParkingTile(tile_id, name, position)

            elif tile_type == "goto_jail":
                tile = GoToJailTile(tile_id, name, position)

            else:
                tile = BaseTile(tile_id, name, position, tile_type)

            tiles.append(tile)
        return tiles

    # ======================================================
    # 2️⃣ DI CHUYỂN & KÍCH HOẠT TILE
    # ======================================================
    def move_player_and_trigger(self, player: Player, steps: int) -> Dict[str, Any]:
        old_pos = player.position
        new_pos = (old_pos + steps) % len(self.tiles)
        passed_go = (old_pos + steps) >= len(self.tiles)

        player.position = new_pos
        tile = self.get_tile(new_pos)

        if passed_go:
            self.bank.pay_player(player,200)

        # Gọi tile.on_land
        raw_result = tile.on_land(player, self.bank)

        # Áp dụng hiệu ứng vào hệ thống
        applied_result = self.apply_tile_effect(player, raw_result)

        # Gộp thêm thông tin cơ bản
        final_event = {
            **applied_result,
            "tile_id": tile.tile_id,
            "tile_name": tile.name,
            "player": player.name,
        }

        return final_event

    # ======================================================
    # 3️⃣ TRUY VẤN BOARD
    # ======================================================
    def get_tile(self, tile_id: int) -> Optional[BaseTile]:
        return next((t for t in self.tiles if t.tile_id == tile_id), None)

    def get_board_state(self) -> Dict[str, Any]:
        return {
            "tiles": [tile.to_dict() for tile in self.tiles],
            "bank": self.bank.serialize_dict()
        }

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.id == player_id), None)

    def get_jail_tile(self):
        return next((t for t in self.tiles if t.tile_type == "jail"), None)

    def send_player_to_jail(self, player: Player) -> Dict[str, Any]:
        jail_tile = self.get_jail_tile()
        if jail_tile:
            player.position = jail_tile.tile_id
            player.is_in_jail = True
            return {"event": "goto_jail", "message": f"{player.name} was sent to jail!"}
        return {"event": "error", "message": "Jail not found on board!"}

    # ======================================================
    # 4️⃣ SERIALIZATION
    # ======================================================
    def serialize_dict(self):
        return self.get_board_state()

    def serialize_json(self):
        return json.dumps(self.get_board_state(), indent=4)
    def apply_tile_effect(self, player: Player, effect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực hiện hiệu ứng được trả về từ tile.on_land().
        - Không thay đổi logic của tile.
        - Cập nhật lại trạng thái Bank/Player/Board nếu có.
        - Trả về event JSON chuẩn cho GameManager/Client.
        """
        event = effect_data.get("event")
        result_packet = {"event": event, "message": "", "updates": {}}

        # 1️⃣ Trường hợp: rút bài Chance / Community Chest
        if event == "DRAW_CARD":
            # Hiệu ứng cụ thể nằm trong effect["effect"]
            card_effect = effect_data.get("effect", {})
            # Gửi packet rút bài (nếu có)
            result_packet["packets"] = effect_data.get("packets", [])
            result_packet["message"] = effect_data.get("message", "")

            # Xử lý hiệu ứng của thẻ (nếu có move_to, add_money, v.v.)
            if "move_to" in card_effect:
                new_pos = card_effect["move_to"]
                player.position = new_pos
                result_packet["updates"]["position"] = new_pos

            if "amount" in card_effect:
                amount = card_effect["amount"]
                if amount < 0:
                    self.bank.pay_bank(player, amount)
                else:
                    self.bank.pay_player(player, amount)
                result_packet["updates"]["balance"] = player.balance

        # 2️⃣ Ô nộp thuế
        elif event == "pay_tax":
            amount = effect_data.get("amount", 0)
            self.bank.collect_tax_or_fee(player, amount)
            result_packet["message"] = f"{player.name} paid ${amount} in tax."
            result_packet["updates"]["balance"] = player.balance

        # 3️⃣ Ô nhận tiền Free Parking
        elif event == "collect_free_parking_money":
            amount = effect_data.get("amount", 0)
            self.bank.pay_free_parking(player)
            result_packet["message"] = f"{player.name} collected ${amount} from Free Parking."
            result_packet["updates"]["balance"] = player.balance

        # 4️⃣ Ô tài sản (Property / Utility / Railroad)
        elif event in ("land_on_property", "land_on_utility", "land_on_railroad"):
            action = effect_data.get("action")
            property_id = effect_data["data"]["property_id"]
            tile = self.get_tile(property_id)

            if action == "buy":
                price = effect_data["data"]["price"]
                self.bank.buy_property(player,tile)
                result_packet["message"] = f"{player.name} bought {tile.name} for ${price}."
                result_packet["updates"]["balance"] = player.balance

            elif action == "pay_rent":
                owner = effect_data["data"]["owner"]
                rent = effect_data["data"]["rent"]
                self.bank.transfer_between_players(player, owner, rent)
                result_packet["message"] = f"{player.name} paid ${rent} rent to {owner.name}."
                result_packet["updates"]["balance"] = player.balance

        # 5️⃣ Ô "Go to Jail"
        elif event == "goto_jail":
            jail_info = self.send_player_to_jail(player)
            result_packet.update(jail_info)
            result_packet["updates"]["position"] = player.position

        # 6️⃣ Trường hợp mặc định
        else:
            result_packet["message"] = effect_data.get("message", "No special effect.")
            result_packet["updates"]["none"] = True

        return result_packet
