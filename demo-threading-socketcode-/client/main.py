 


# src/client/main.py
import threading
import time
from .network import ClientNetwork

def on_msg(pkt):
    t = pkt.get('type')
    if t == 'CHAT':
        print(f"[{pkt.get('name')}] {pkt.get('message')}")

def main():
    name = input("Your name: ").strip() or "anon"
    client = ClientNetwork(host='127.0.0.1', port=12345, on_message=on_msg)
    client.connect()
    client.send({'type':'JOIN', 'name': name})
    try:
        while True:
            line = input()
            if line.strip().lower() in ('/exit', '/quit'):
                client.send({'type':'EXIT', 'name': name})
                break
            if not line:
                continue
            client.send({'type':'CHAT', 'message': line})
    except KeyboardInterrupt:
        client.send({'type':'EXIT', 'name': name})
    finally:
        client.close()

if __name__ == '__main__':
    main()
