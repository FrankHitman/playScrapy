import scrapy
import os
from scrapy_playwright.page import PageMethod


level_urls = {
    "level03": [
        f"https://tsunagarujp.mext.go.jp/level03/c{i:02d}?lang_id=ZH" for i in range(18, 20)
        # f"https://tsunagarujp.mext.go.jp/level03/c{i:02d}?lang_id=ZH" for i in range(1, 20)
    ],
    # "level02": [
    #     f"https://tsunagarujp.mext.go.jp/level02/b{i:02d}?lang_id=ZH" for i in range(1, 20)
    # ],
    # "level01": [
    #     f"https://tsunagarujp.mext.go.jp/level01/a{i:02d}?lang_id=ZH" for i in range(1, 13)
    # ],
    "level00": [
        f"https://tsunagarujp.mext.go.jp/level00/d{i:02d}?lang_id=ZH" for i in range(5, 7)
        # f"https://tsunagarujp.mext.go.jp/level00/d{i:02d}?lang_id=ZH" for i in range(1, 7)
    ]
}

class TsunagaruSpider(scrapy.Spider):
    name = "tsunagaru"
    # custom_settings = {
    #     "DOWNLOAD_HANDLERS": {
    #         "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #         "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    #     },
    #     "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    #     "PLAYWRIGHT_BROWSER_TYPE": "chromium",
    # }
    # https://tsunagarujp.mext.go.jp/api/v1/phrase?lang_type=ZH&page_id=LEVEL00-03&level_id=0&scene_number=3
    # this api is loading the data of the chatting script. 
    # but in some cases, the response is 500. so config AUTOTHROTTLE_ENABLED to True.
    # filter out the static resource request, such as: png, jpg, jpeg, gif, svg, woff, woff2.
    def start_requests(self):
        for _, urls in level_urls.items():
            for url in urls:
                yield scrapy.Request(
                    url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("route", "**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort()),
                            PageMethod("wait_for_load_state", "networkidle", timeout=180000),
                            # PageMethod("wait_for_load_state", "load", timeout=60000),   # timeout=120000 fix c19 load failed, but the script is empty
                        ],
                        "playwright_page_close": True,  # 爬完自动关闭页面
                    }
                )

    def parse(self, response):
        # response.text 就是渲染后的 HTML
        self.logger.info(f"抓取到页面: {response.url}")
        level = response.url.split('/')[-2]
        level_num = response.url.split('/')[-1].split('?')[0]
        file_path = f"{level}/tsunagaru_{level}_{level_num}.html"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)