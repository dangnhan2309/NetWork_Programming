import json
from pathlib import Path


def load_property_data_from_file(json_file_path):
    """
    Tải danh sách cấu hình các ô đất từ tệp JSON.

    Args:
        json_file_path (str): Đường dẫn đến tệp JSON.

    Returns:
        list: Danh sách các dictionary chứa dữ liệu ô đất.

    Raises:
        FileNotFoundError: Nếu tệp không tồn tại.
    """
    json_path = Path(json_file_path)

    # 1. Kiểm tra sự tồn tại của tệp
    if not json_path.exists():
        # Dùng raise để báo lỗi nếu không tìm thấy
        raise FileNotFoundError(f"Không tìm thấy tệp cấu hình bàn cờ tại: {json_path}")

    # 2. Mở và tải dữ liệu
    with open(json_path, 'r', encoding='utf-8') as f:
        # Giả định tệp JSON chứa một danh sách các dictionary (như dữ liệu đầy đủ bạn đã tạo)
        data = json.load(f)

    print(f"✅ Đã tải thành công {len(data)} cấu hình ô đất từ: {json_path.name}")
    return data