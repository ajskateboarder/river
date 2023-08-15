
from websockets.sync.client import connect
with connect("ws://localhost:8001", max_size=None) as websocket:
    websocket.send("https://www.amazon.com/s?k=laptop")
    message = websocket.recv()
    print(f"Received: {message}")
