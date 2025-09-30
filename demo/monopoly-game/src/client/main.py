# # src/client/main.py
# import asyncio
# from .network import Client
# from .ui import ClientUI
#
#
# async def main():
#     # Khởi tạo client + UI
#     uri = "ws://localhost:8765"
#     name = input("Enter your player name: ") or "Guest"
#
#     client = Client(uri=uri, name=name)
#     client.ui = ClientUI()   # gắn UI
#
#     print("\n=== Monopoly Client Started ===")
#     print("👉 Commands: JOIN, ROLL, CHAT, EXIT")
#     print("==============================\n")
#
#     await client.run()
#
#
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\n[CLIENT] Exiting...")
# src/client/main.py
import asyncio
from .network import Client   # import Client đã viết ở client.py

async def main():
<<<<<<< Updated upstream
    # Tạo client mới, có thể chỉnh name cho dễ phân biệt
    IP = str(input("Enter Ip server: "))
    Port = str(input("Enter Port server: "))
    Name = str(input("Enter Nick Name: "))
=======
    # Lấy địa chỉ server từ command line hoặc dùng mặc định
    server_host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    server_port = sys.argv[2] if len(sys.argv) > 2 else "8765"
    # -> nhận room ip tên
    uri = f"ws://{server_host}:{server_port}"
    
    print(f"🎮 Kết nối đến server: {uri}")
    
    client = MonopolyClient(uri)
    
>>>>>>> Stashed changes
    try:
        client = Client(uri=f"ws://{IP}:{Port}", name=f"{Name}")
        await client.run()
        print("✅ Connection successful")
    except ConnectionRefusedError:
        print(f"❌ Connection failed. Could not connect to {IP}:{Port}. Please check if the server is running and the IP/Port are correct.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")



if __name__ == "__main__":
    asyncio.run(main())

