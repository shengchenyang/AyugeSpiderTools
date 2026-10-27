from __future__ import annotations

from typing import TYPE_CHECKING, cast

from scrapy import signals

from ayugespidertools.exceptions import NotConfigured

if TYPE_CHECKING:
    from typing import Self

    from scrapy import Request
    from scrapy.crawler import Crawler

    from ayugespidertools.spiders import AyuSpider


class ProxyDownloaderMiddleware:
    """Example of proxy middleware"""

    proxy: str
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        s.crawler = crawler
        return s

    def process_request(self, request: Request) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        if not hasattr(spider, "proxy_conf"):
            raise NotConfigured(
                "[proxy] section is not configured in either .conf or remote config."
            )
        request.meta["proxy"] = self.proxy

    def spider_opened(self, spider: AyuSpider) -> None:
        spider.slog.info(
            f"代理中间件: ProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}"
        )
        self.proxy = spider.proxy_conf.proxy
