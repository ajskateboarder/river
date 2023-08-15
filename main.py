import asyncio
import functools
from urllib.parse import quote_plus

import websockets

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from webdriver_manager.firefox import GeckoDriverManager


class Amazon:
    def __init__(self) -> None:
        opts = Options()
        opts.add_argument("--headless")
        self.driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()), options=opts
        )

    def ids(self, query):
        self.driver.get(f"https://www.amazon.com/s?k={quote_plus(query)}")
        self.driver.execute_script(f"window.scrollBy(0, 1000)")
        return self.driver.find_element("id", "search").get_attribute("innerHTML")

@functools.lru_cache()
def browser():
    return Amazon()

async def handler(websocket):
    async for message in websocket:
        await websocket.send(browser().ids(message))

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
