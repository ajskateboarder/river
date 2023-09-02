import functools
from itertools import repeat, count, zip_longest
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from websockets.sync.server import serve
from websockets.sync.server import ServerConnection

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

from webdriver_manager.firefox import GeckoDriverManager

class Amazon:
    # adapted from wordsmyth crawling
    def __init__(self) -> None:
        opts = Options()
        opts.add_argument("--headless")
        path = GeckoDriverManager().install()
        with ThreadPoolExecutor() as executor:
            self.browsers = list(
                map(
                    lambda fut: fut.result(),
                    as_completed(
                        [executor.submit(webdriver.Firefox, service=Service(path), options=opts) for _ in range(5)]
                    ),
                )
        )

    @staticmethod
    def select_reviews(content):
        for review in content:
            row = review.select_one(".a-row")
            if row is not None:
                rating = int(
                    row.select_one("i[data-hook='review-star-rating']").text.split(".")[
                        0
                    ]
                )
                body = row.select_one("span[data-hook='review-body']").text
                yield {"reviewText": body.strip(), "overall": rating}

    def _login_single(self, browser, email, password) -> None:
        browser.get("https://amazon.com")
        try:
            browser.find_element("id", "nav-link-accountList").click()
            browser.find_element("id", "ap_email").send_keys(email)
            browser.find_element("id", "continue").click()
            browser.find_element("id", "ap_password").send_keys(password)
            browser.find_element("id", "signInSubmit").click()
        except Exception:
            self._login_single(browser, email, password)

    def login(self, email: str, password: str) -> None:
        with ThreadPoolExecutor() as executor:
            executor.map(
                self._login_single,
                self.browsers,
                repeat(email),
                repeat(password),
            )

    def proportions(
        self, asin: str, total: int = 500
    ):
        self.browsers[1].get(f"https://amazon.com/product-reviews/{asin}")

        percentages = self.browsers[1].find_element(
            "css selector", ".histogram"
        ).text.split("\n")[1::2]
        parsed = list(map(lambda p: int(p.replace("%", "")) / 100, percentages))
        if total is None:
            return parsed
        parsed = list(map(lambda x: x * 500, parsed))
        while any(x > 100 for x in parsed):
            parsed = list(map(lambda x: x * 0.99, parsed))
        return list(reversed(list(map(lambda x: int(x) + 1, parsed))))

    def _scrape_single(
        self,
        browser,
        asin,
        category: int,
        callback,
        limit,
    ) -> None:
        map_star = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}

        if limit:
            counter = count(0)
        for page in range(1, 11):
            browser.get(
                f"https://www.amazon.com/product-reviews/{asin}/"
                f"?ie=UTF8&reviewerType=all_reviews&pageNumber={page}&filterByStar={map_star[category]}"
            )
            soup = BeautifulSoup(browser.page_source, "html.parser")
            content = soup.select("div[data-hook='review']")
            for item in self.select_reviews(content):
                if next(counter) >= limit:  # type: ignore
                    return
                callback({**item, "productId": asin})

    def scrape(
        self,
        asin,
        callback,
        proportions,
    ) -> None:
        if not proportions:
            proportions = []

        with ThreadPoolExecutor() as executor:
            for i, browser, prop in zip_longest(
                range(1, 6), self.browsers, proportions
            ):
                # ctx = get_script_run_ctx()
                future = executor.submit(
                    self._scrape_single,
                    browser,
                    asin,
                    i,
                    callback,
                    prop,  # ctx
                )
                if future.exception():
                    raise future.exception()

@functools.lru_cache()
def browser():
    return Amazon()

def handler(websocket: ServerConnection):
    def send(message, typ):
        websocket.send(json.dumps({**message, "type": typ}))
    for message in websocket:
        data = json.loads(message)
        if data["command"] == "login":
            send({"message": "Logging in..."}, "status")
            browser().login(data["username"], data["password"])
            send({"message": "Logging in done"}, "status")
        if data["command"] == "scrape":
            props = browser().proportions(data["asin"])
            browser().scrape(data["asin"], functools.partial(send, typ="response"), props)

def main():
    with serve(handler, "", 8001) as server:
        server.serve_forever()

if __name__ == "__main__":
    main()
