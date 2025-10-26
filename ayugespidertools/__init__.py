from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.config import logger
from ayugespidertools.items import AyuItem
from ayugespidertools.scraper.http.request.aiohttp import AiohttpRequest
from ayugespidertools.scraper.spiders import AyuSpider
from ayugespidertools.scraper.spiders.crawl import AyuCrawlSpider

__all__ = [
    "AiohttpRequest",
    "AyuCrawlSpider",
    "AyuItem",
    "AyuSpider",
    "PortalTag",
    "__version__",
    "logger",
]

__version__ = "3.13.3"
