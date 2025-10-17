from typing import Dict,Any
from .BaseProperty import BaseProperty
class RailroadProperty(BaseProperty):
    """Đại diện cho các ô Ga Tàu Hỏa."""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

        # Thuộc tính cụ thể của Railroad (lấy từ property_info)
        info = data.get('property_info', {})
        # Ví dụ: {"1_owned": 25, "2_owned": 50, ...}
        self.rent_tiers: Dict[str, int] = info.get('rent_tiers', {})

        # Cần truyền 'railroad_count' (số lượng ga mà chủ sở hữu nắm giữ)

    def calculate_rent(self, railroad_count: int, **kwargs) -> int:
        if self.is_mortgaged:
            return 0

        key = f"{railroad_count}_owned"
        return self.rent_tiers.get(key, 0)