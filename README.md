# Crawl content from Japanese leaning website by scrapy

## Environment preparation

```
pyenv local 3.11.8
pip install virtualenv
virtualenv .venv
source .venv/bin/activate
pip install scrapy
scrapy startproject play_scrapy
cd play_scrapy/
scrapy crawl quotes
pip install pytest-playwright
pip install pytest-playwright playwright -U
playwright install
pip install scrapy-playwright
scrapy crawl tsunagaru
pip freeze > requirements.txt 

```

### Some notes
first impression of scrapy
```
MacBook-Pro:playPython frank$ scrapy shell "https://quotes.toscrape.com/page/1/"
2025-06-18 20:20:50 [scrapy.utils.log] INFO: Scrapy 2.13.2 started (bot: scrapybot)
2025-06-18 20:20:50 [scrapy.utils.log] INFO: Versions:
{'lxml': '5.4.0',
 'libxml2': '2.13.8',
 'cssselect': '1.3.0',
 'parsel': '1.10.0',
 'w3lib': '2.3.1',
 'Twisted': '25.5.0',
 'Python': '3.11.8 (main, Jun 18 2025, 17:55:08) [Clang 17.0.0 '
           '(clang-1700.0.13.3)]',
 'pyOpenSSL': '25.1.0 (OpenSSL 3.5.0 8 Apr 2025)',
 'cryptography': '45.0.4',
 'Platform': 'macOS-15.4.1-x86_64-i386-64bit'}
2025-06-18 20:20:50 [scrapy.addons] INFO: Enabled addons:
[]
2025-06-18 20:20:50 [asyncio] DEBUG: Using selector: KqueueSelector
2025-06-18 20:20:50 [scrapy.utils.log] DEBUG: Using reactor: twisted.internet.asyncioreactor.AsyncioSelectorReactor
2025-06-18 20:20:50 [scrapy.utils.log] DEBUG: Using asyncio event loop: asyncio.unix_events._UnixSelectorEventLoop
2025-06-18 20:20:50 [scrapy.extensions.telnet] INFO: Telnet Password: 961c57a22523fb9b
2025-06-18 20:20:50 [scrapy.middleware] INFO: Enabled extensions:
['scrapy.extensions.corestats.CoreStats',
 'scrapy.extensions.telnet.TelnetConsole',
 'scrapy.extensions.memusage.MemoryUsage']
2025-06-18 20:20:50 [scrapy.crawler] INFO: Overridden settings:
{'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
 'LOGSTATS_INTERVAL': 0}
2025-06-18 20:20:50 [scrapy.middleware] INFO: Enabled downloader middlewares:
['scrapy.downloadermiddlewares.offsite.OffsiteMiddleware',
 'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware',
 'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware',
 'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware',
 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware',
 'scrapy.downloadermiddlewares.retry.RetryMiddleware',
 'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware',
 'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware',
 'scrapy.downloadermiddlewares.redirect.RedirectMiddleware',
 'scrapy.downloadermiddlewares.cookies.CookiesMiddleware',
 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware',
 'scrapy.downloadermiddlewares.stats.DownloaderStats']
2025-06-18 20:20:50 [scrapy.middleware] INFO: Enabled spider middlewares:
['scrapy.spidermiddlewares.start.StartSpiderMiddleware',
 'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware',
 'scrapy.spidermiddlewares.referer.RefererMiddleware',
 'scrapy.spidermiddlewares.urllength.UrlLengthMiddleware',
 'scrapy.spidermiddlewares.depth.DepthMiddleware']
2025-06-18 20:20:50 [scrapy.middleware] INFO: Enabled item pipelines:
[]
2025-06-18 20:20:50 [scrapy.extensions.telnet] INFO: Telnet console listening on 127.0.0.1:6023
2025-06-18 20:20:50 [scrapy.core.engine] INFO: Spider opened
2025-06-18 20:20:52 [scrapy.core.engine] DEBUG: Crawled (200) <GET https://quotes.toscrape.com/page/1/> (referer: None)
[s] Available Scrapy objects:
[s]   scrapy     scrapy module (contains scrapy.Request, scrapy.Selector, etc)
[s]   crawler    <scrapy.crawler.Crawler object at 0x112479d10>
[s]   item       {}
[s]   request    <GET https://quotes.toscrape.com/page/1/>
[s]   response   <200 https://quotes.toscrape.com/page/1/>
[s]   settings   <scrapy.settings.Settings object at 0x112496610>
[s] Useful shortcuts:
[s]   fetch(url[, redirect=True]) Fetch URL and update local objects (by default, redirects are followed)
[s]   fetch(req)                  Fetch a scrapy.Request and update local objects 
[s]   shelp()           Shell help (print this help)
[s]   view(response)    View response in a browser
>>> 
```
when using `view(response)` to check content of "https://tsunagarujp.mext.go.jp/level03/c01/", 
the webpage is not fully loaded. So that introduce playwright to load javascript generated content.

while scrapy is a async framework, example in spiders/scrape_tsunagaru.py is a sync function.
so that introduce scrapy-playwright plugin to integate playwright into scrapy.



### Todo
- there are tsunagaru_18~19 crawled failed, find the reason and fix.
- integrate data extract into scrapy 
- all other leve chatting scrips, such as: level02
- crawl the video