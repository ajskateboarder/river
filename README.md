# river

This just sets up a silent Amazon data scraper with Firefox and Selenium and runs under a WebSocket API

It's very simple, and it's just for some stuff that I'm doing

## Building locally

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pyi-makespec main.py --onefile --noconsole
pyinstaller --clean main.spec
```

Check `dist/` for an executable
