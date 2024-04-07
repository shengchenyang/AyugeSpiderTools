# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from ayugespidertools.scraper.middlewares.headers.ua import RandomRequestUaMiddleware
from ayugespidertools.scraper.middlewares.netlib.aiohttplib import (
    AiohttpDownloaderMiddleware,
)
from ayugespidertools.scraper.middlewares.proxy.dynamic import (
    AbuDynamicProxyDownloaderMiddleware,
    DynamicProxyDownloaderMiddleware,
)
from ayugespidertools.scraper.middlewares.proxy.exclusive import (
    ExclusiveProxyDownloaderMiddleware,
)

__all__ = [
    "RandomRequestUaMiddleware",
    "AiohttpDownloaderMiddleware",
    "DynamicProxyDownloaderMiddleware",
    "AbuDynamicProxyDownloaderMiddleware",
    "ExclusiveProxyDownloaderMiddleware",
]
