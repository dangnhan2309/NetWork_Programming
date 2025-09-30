# 🚀 QUICK START - Monopoly Multiplayer Game

## 📋 Yêu cầu
- Python 3.7+
- websockets library

## 🛠️ Cài đặt nhanh

```bash
# 1. Cài đặt dependencies
pip install websockets

# 2. Test hệ thống
python demo.py
```

## 🎮 Chạy game

### Terminal 1 - Server
```bash
python run_server.py
```

### Terminal 2 - Client 1
```bash
python run_client.py
```

### Terminal 3 - Client 2
```bash
python run_client.py
```

## 🎯 Cách chơi

1. **Kết nối**: Gõ `/join <tên>` để tham gia
2. **Chơi**: 
   - `/roll` - Gieo xúc xắc
   - `/buy` - Mua property
   - `/pay <player> <amount>` - Trả tiền
   - `/end` - Kết thúc lượt
3. **Chat**: Gõ text thường để chat

## 🎲 Game Flow

1. **Waiting** ⏳: Chờ đủ 2+ players
2. **Playing** 🎮: Game bắt đầu, lần lượt từng player
3. **Real-time** 🔄: Đồng bộ trạng thái tự động

## 🐛 Troubleshooting

- **Import Error**: Chạy từ thư mục `demo/monopoly-game/`
- **Connection Error**: Kiểm tra server đã chạy chưa
- **Port Error**: Đổi port trong code nếu cần

## 📁 Cấu trúc

```
src/
├── shared/constants.py    # Protocol & constants
├── server/
│   ├── network.py        # WebSocket server
│   ├── game_manager.py   # Game logic
│   ├── player.py         # Player class
│   └── board.py          # Board class
└── client/
    ├── main.py           # Client main
    ├── commands.py       # Command parser
    └── ui.py             # Console UI
```

## 🎉 Enjoy the game!
