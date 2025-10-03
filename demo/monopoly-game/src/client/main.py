import asyncio
from .network import MonopolyClient

async def main():
    import sys
    
    # Lấy URI từ command line hoặc dùng mặc định
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:12345"
    
    client = MonopolyClient(uri)
    
    try:
        await client.run()
    except KeyboardInterrupt:
        print("\n👋 Tạm biệt!")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    import random
    asyncio.run(main())