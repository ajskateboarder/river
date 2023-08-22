# river

This just sets up a silent Amazon data scraper with Firefox and Selenium and runs under a WebSocket API.

It's very simple, and it's just for some stuff that I'm doing

## Building locally

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pyi-makespec main.py --onefile --noconsole
pyinstaller --clean main.spec
```

Check `dist/` for an executable. Running the EXE should start the server on `ws://localhost:8001`

## Usage

Connect to the server using any WebSocket client and send a URL.

```py
from websockets.sync.client import connect
with connect("ws://localhost:8001", max_size=None) as websocket:
    websocket.send("https://www.amazon.com/s?k=laptop")
    message = websocket.recv() # should be a bunch of HTML
    with open("document.html", "w", encoding="utf-8") as fh:
        fh.write(message)
```

## Possible errors

On Windows, you might get this error:

```text
OSError: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8001): only one usage of each socket address (protocol/network address/port) is normally permitted
```

even though the server has not been started already. To solve this, make sure you give the app permissions to access features on public/private networks:

> ![stupid-windows-defender](./media/warning.png)
