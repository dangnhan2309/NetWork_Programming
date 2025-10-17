from typing import Dict,Any
from .BaseProperty import BaseProperty
class UtilityProperty(BaseProperty):
    """Đại diện cho các ô Công Ty Tiện Ích."""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

        # Thuộc tính cụ thể của Utility (lấy từ property_info)
        info = data.get('property_info', {})
        # Ví dụ: {"1_owned": 4, "2_owned": 10}
        self.rent_multipliers: Dict[str, int] = info.get('rent_multipliers', {})

    # Cần truyền 'utility_count' và 'dice_roll'
    def calculate_rent(self, utility_count: int, dice_roll: int, **kwargs) -> int:

        if self.is_mortgaged:
            return 0
        key = f"{utility_count}_owned"
        multiplier = self.rent_multipliers.get(key, 0)

        # Tiền thuê = Hệ số nhân * Số nút xúc xắc
        return multiplier * dice_roll
