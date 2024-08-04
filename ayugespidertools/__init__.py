from ayugespidertools.config import logger
from ayugespidertools.items import AyuItem
from ayugespidertools.scraper.http.request import AiohttpRequest
from ayugespidertools.scraper.http.request.form import AiohttpFormRequest
from ayugespidertools.scraper.spiders import AyuSpider
from ayugespidertools.scraper.spiders.crawl import AyuCrawlSpider

__all__ = [
    "AiohttpRequest",
    "AiohttpFormRequest",
    "AyuItem",
    "AyuSpider",
    "AyuCrawlSpider",
    "logger",
    "__version__",
]

__version__ = "3.9.8"
