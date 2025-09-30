import asyncio
from .network import GameServer



def main ():
    try :
        server = GameServer()
        asyncio.run(server.start())
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
