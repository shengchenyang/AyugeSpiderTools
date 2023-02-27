# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from ayugespidertools.scraper.middlewares.headers.ua import RandomRequestUaMiddleware
from ayugespidertools.scraper.middlewares.netlib.requestslib import (
    RequestByRequestsMiddleware,
)
from ayugespidertools.scraper.middlewares.proxy.dynamic import (
    AbuDynamicProxyDownloaderMiddleware,
    DynamicProxyDownloaderMiddleware,
)
from ayugespidertools.scraper.middlewares.proxy.exclusive import (
    ExclusiveProxyDownloaderMiddleware,
)
from ayugespidertools.scraper.middlewares.proxy.private import (
    PrivateProxyDownloaderMiddleware,
)

__all__ = [
    "RandomRequestUaMiddleware",
    "RequestByRequestsMiddleware",
    "DynamicProxyDownloaderMiddleware",
    "AbuDynamicProxyDownloaderMiddleware",
    "ExclusiveProxyDownloaderMiddleware",
    "PrivateProxyDownloaderMiddleware",
]
