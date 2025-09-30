# 🎲 Monopoly Multiplayer Game

Game Monopoly multiplayer sử dụng WebSocket, hỗ trợ kết nối nhiều client và đồng bộ trạng thái game real-time.

## 🚀 Tính năng

- **Multiplayer**: Hỗ trợ tối đa 4 người chơi
- **Real-time**: Đồng bộ trạng thái game real-time qua WebSocket
- **Console UI**: Giao diện console đẹp mắt với emoji
- **Game Commands**: Đầy đủ lệnh game (ROLL, BUY, PAY, END_TURN)
- **Chat System**: Chat giữa các người chơi
- **Auto Game Management**: Tự động quản lý lượt chơi và trạng thái

## 📋 Yêu cầu

- Python 3.7+
- websockets library

## 🛠️ Cài đặt

1. **Clone repository**:
```bash
git clone <repository-url>
cd demo/monopoly-game
```

2. **Cài đặt dependencies**:
```bash
pip install -r requirements.txt
```

## 🎮 Cách chạy

### 1. Chạy Server

```bash
cd src/server
python main.py
```

Server sẽ chạy trên `ws://localhost:8765`

### 2. Chạy Client

Mở terminal mới cho mỗi người chơi:

```bash
cd src/client
python main.py
```

## 🎯 Cách chơi

### Kết nối
1. Chạy server trước
2. Chạy client cho mỗi người chơi
3. Gõ `/join <tên>` để tham gia game

### Lệnh game
- `/roll` - Gieo xúc xắc và di chuyển
- `/buy` - Mua property đang đứng (nếu được)
- `/pay <player> <amount>` - Trả tiền cho player khác
- `/end` - Kết thúc lượt chơi
- `/state` - Xem trạng thái game hiện tại

### Chat
- Gõ text thường để chat
- `/say <text>` hoặc `/chat <text>` để chat

### Lệnh khác
- `/help` - Hiển thị hướng dẫn
- `/exit` - Thoát game

## 🏗️ Cấu trúc dự án

```
src/
├── shared/
│   ├── constants.py      # Hằng số và protocol
│   └── protocol.py       # Protocol xử lý message
├── server/
│   ├── main.py          # Server main
│   ├── network.py       # WebSocket server
│   ├── game_manager.py  # Quản lý game logic
│   ├── player.py        # Player class
│   ├── board.py         # Board game
│   └── tiles.py         # Tile definitions
└── client/
    ├── main.py          # Client main
    ├── commands.py      # Parse lệnh client
    ├── network.py       # WebSocket client
    └── ui.py            # Console UI
```

## 🔧 Cấu hình

Các thông số có thể điều chỉnh trong `src/shared/constants.py`:

- `MAX_PLAYERS = 4` - Số người chơi tối đa
- `TURN_TIMEOUT_SEC = 60` - Timeout cho mỗi lượt
- `BOARD_SIZE = 40` - Kích thước board
- `STARTING_MONEY = 1500` - Tiền ban đầu

## 🎲 Game Flow

1. **Waiting**: Chờ đủ 2+ người chơi
2. **Playing**: Game bắt đầu, lần lượt từng người chơi
3. **Turn Management**: Tự động chuyển lượt sau mỗi action
4. **State Sync**: Đồng bộ trạng thái real-time cho tất cả client

## 🐛 Troubleshooting

### Lỗi kết nối
- Kiểm tra server đã chạy chưa
- Kiểm tra port 8765 có bị block không
- Kiểm tra firewall settings

### Lỗi import
- Đảm bảo chạy từ đúng thư mục
- Kiểm tra Python path
- Cài đặt đầy đủ dependencies

## 📝 Ghi chú

- Game sử dụng WebSocket để real-time communication
- State được đồng bộ tự động giữa tất cả clients
- Console UI được thiết kế để dễ đọc và tương tác
- Hỗ trợ chat giữa các người chơi

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Hãy tạo issue hoặc pull request.

## 📄 License

MIT License