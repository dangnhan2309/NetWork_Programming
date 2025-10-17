from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProperty(ABC):
    """
    Lớp cơ sở trừu tượng cho mọi loại tài sản Monopoly.
    Lưu trữ thông tin tài chính và trạng thái sở hữu chung.
    """

    def __init__(self, data: Dict[str, Any]):
        # --- Thông tin chung ---
        self.name: str = data['name']
        self.type: str = data.get('type', 'property')  # Ví dụ: 'property', 'railroad', 'utility'
        self.color_group: str = data.get('color_group', data.get('color'))

        # Lấy thông tin từ trường 'property_info' nếu có (áp dụng cho RR/Utility)
        info = data.get('property_info', {})

        # --- Tài chính chung (luôn có) ---
        self.purchase_price: int = data.get('price', info.get('purchase_price'))
        self.mortgage_value: int = info.get('mortgage_value', 0)

        # --- Trạng thái hiện tại ---
        self.is_mortgaged: bool = False
        self.owner = None

    @abstractmethod
    def calculate_rent(self, **kwargs) -> int | None:
        """
        Phương thức trừu tượng: bắt buộc các lớp con phải tự định nghĩa logic tính tiền thuê
        phù hợp với loại tài sản đó.
        """
        if self.is_mortgaged:
            return 0
        return None

    def __str__(self):
        owner_name = self.owner.name if self.owner else "Ngân hàng"
        return f"{self.name} ({self.type.capitalize()}) | Giá: ${self.purchase_price} | Chủ: {owner_name}"