class Server():
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        print(f"Server starting on {self.host}:{self.port}")
        