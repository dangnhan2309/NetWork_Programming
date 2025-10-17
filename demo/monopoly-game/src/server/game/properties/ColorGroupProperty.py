from typing import Dict, Any
from .BaseProperty import BaseProperty
class ColorGroupProperty(BaseProperty):
    """Đại diện cho các ô đất màu có thể xây Nhà/Khách sạn."""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        # --- Thuộc tính cụ thể của Color Group ---
        self.base_rent: int = data['base_rent']
        self.rents: Dict[str, int] = data['rents']
        self.house_cost: int = data['building_costs']['house_cost']
        self.hotel_cost: int = data['building_costs']['hotel_cost']

        # --- Trạng thái xây dựng ---
        self.houses: int = 0
        self.has_hotel: bool = False

    def calculate_rent(self, is_monopoly: bool = False, **kwargs) -> int:
        # Nếu đang cầm cố, tiền thuê là 0
        if self.is_mortgaged:
            return 0

        # Ưu tiên Khách sạn
        if self.has_hotel:
            return self.rents['hotel']

        # Tiền thuê theo số lượng Nhà
        if self.houses > 0:
            rent_key = f"{self.houses}_house" if self.houses == 1 else f"{self.houses}_houses"
            return self.rents.get(rent_key, 0)

        # Đất chưa cải tạo (Unimproved Lot)
        rent = self.base_rent
        if is_monopoly:
            # Quy tắc Monopoly: Tiền thuê nhân đôi trên đất trống
            return rent * 2
        else:
            return rent

    def __str__(self):
        details = f"| Nhà: {self.houses} | KS: {self.has_hotel}"
        return super().__str__() + details