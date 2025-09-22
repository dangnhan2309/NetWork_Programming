@echo off
REM === Tạo thư mục chính ===
mkdir monopoly-game
cd monopoly-game

REM === Các thư mục con ===
mkdir docs
mkdir config
mkdir src
mkdir src\server
mkdir src\client
mkdir src\shared
mkdir tests
mkdir scripts

REM === Tạo file rỗng ===
echo # Monopoly Multiplayer Project > README.md
echo. > requirements.txt

echo # Config settings > config\settings.yaml

echo. > src\server\__init__.py
echo. > src\server\main.py
echo. > src\server\game_manager.py
echo. > src\server\player.py
echo. > src\server\board.py
echo. > src\server\network.py
echo. > src\server\utils.py

echo. > src\client\__init__.py
echo. > src\client\main.py
echo. > src\client\ui.py
echo. > src\client\network.py
echo. > src\client\commands.py

echo. > src\shared\__init__.py
echo. > src\shared\protocol.py
echo. > src\shared\constants.py

echo. > tests\test_game_manager.py
echo. > tests\test_network.py
echo. > tests\test_client_server.py

echo @echo off > scripts\run_server.bat
echo python src\server\main.py >> scripts\run_server.bat

echo @echo off > scripts\run_client.bat
echo python src\client\main.py >> scripts\run_client.bat

echo === Done! Project structure created at %cd% ===
pause
