from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.config import logger
from ayugespidertools.items import AyuItem
from ayugespidertools.scraper.http.request.aiohttp import AiohttpRequest
from ayugespidertools.scraper.spiders import AyuSpider
from ayugespidertools.scraper.spiders.crawl import AyuCrawlSpider

__all__ = [
    "PortalTag",
    "AiohttpRequest",
    "AyuItem",
    "AyuSpider",
    "AyuCrawlSpider",
    "logger",
    "__version__",
]

__version__ = "3.12.2"
