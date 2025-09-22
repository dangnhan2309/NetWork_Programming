monopoly-game/
│── docs/                     # Tài liệu thiết kế, đặc tả, kiến trúc
│   └── README.md
│
│── config/                   # Cấu hình (port, IP, tham số game)
│   └── settings.yaml
│
│── src/
│   ├── server/               # Code server (quản lý game logic, socket)
│   │   ├── __init__.py
│   │   ├── main.py           # Entry point để chạy server
│   │   ├── game_manager.py   # Quản lý board, lượt chơi, luật
│   │   ├── player.py         # Class Player
│   │   ├── board.py          # Class Board, Property
│   │   ├── network.py        # Quản lý socket, protocol JSON
│   │   └── utils.py
│   │
│   ├── client/               # Code client (console UI + socket)
│   │   ├── __init__.py
│   │   ├── main.py           # Entry point chạy client
│   │   ├── ui.py             # In ra console (hoặc sau này GUI)
│   │   ├── network.py        # Client socket
│   │   └── commands.py       # Xử lý input từ người chơi
│   │
│   └── shared/               # Code dùng chung (protocol, message types)
│       ├── __init__.py
│       ├── protocol.py       # JSON schema cho message
│       └── constants.py
│
│── tests/                    # Unit test & integration test
│   ├── test_game_manager.py
│   ├── test_network.py
│   └── test_client_server.py
│
│── scripts/                  # Script tiện ích (khởi chạy, deploy)
│   ├── run_server.sh
│   ├── run_client.sh
│   └── dev_tools.py
│
│── requirements.txt          # Thư viện Python cần cài
│── pyproject.toml / setup.py # Nếu muốn đóng gói
│── README.md                 # Hướng dẫn chạy dự án
