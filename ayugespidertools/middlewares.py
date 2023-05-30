from ayugespidertools.scraper.middlewares.headers.ua import RandomRequestUaMiddleware
from ayugespidertools.scraper.middlewares.netlib.aiohttplib import (
    AiohttpAsyncDownloaderMiddleware,
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
    "AiohttpAsyncDownloaderMiddleware",
    "AiohttpDownloaderMiddleware",
    "AbuDynamicProxyDownloaderMiddleware",
    "DynamicProxyDownloaderMiddleware",
    "ExclusiveProxyDownloaderMiddleware",
]
