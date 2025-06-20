from collections.abc import AsyncIterator
from typing import Any, AsyncIterator
import scrapy
from scrapy_playwright.page import PageMethod

urls = [
    f"https://tsunagarujp.mext.go.jp/level03/c{i:02d}?lang_id=ZH" for i in range(1, 19)
]

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

    def start_requests(self):
        for url in urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                    "playwright_page_close": True,  # 爬完自动关闭页面
                }
            )

    def parse(self, response):
        # response.text 就是渲染后的 HTML
        self.logger.info(f"抓取到页面: {response.url}")
        # 你可以在这里解析数据
        # 比如保存到文件
        with open(f"tsunagaru_{response.url.split('c')[-1]}.html", "w", encoding="utf-8") as f:
            f.write(response.text)