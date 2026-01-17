from __future__ import annotations

import base64
from typing import TYPE_CHECKING, cast

from scrapy import signals

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param

if TYPE_CHECKING:
    from scrapy import Request
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class DynamicProxyDownloaderMiddleware:
    """动态隧道代理中间件"""

    proxy_url: str
    username: str
    password: str
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        s.crawler = crawler
        return s

    def process_request(self, request: Request) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        if request.url.startswith("https://"):
            request.meta["proxy"] = (
                f"https://{self.username}:{self.password}@{self.proxy_url}/"
            )
        elif request.url.startswith("http://"):
            request.meta["proxy"] = (
                f"http://{self.username}:{self.password}@{self.proxy_url}/"
            )
        else:
            spider.slog.info(
                f"request url: {request.url} error when use proxy middlewares!"
            )

        # 避免因连接复用导致隧道不能切换 IP
        request.headers["Connection"] = "close"
        # 采用 gzip 压缩加速访问
        request.headers["Accept-Encoding"] = "gzip"

    def spider_opened(self, spider: AyuSpider) -> None:
        spider.slog.info(
            f"动态隧道代理中间件: DynamicProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}"
        )

        self.proxy_url = spider.dynamicproxy_conf.proxy
        self.username = spider.dynamicproxy_conf.username
        self.password = spider.dynamicproxy_conf.password


class AbuDynamicProxyDownloaderMiddleware:
    """阿布云动态代理 - 隧道验证方式（其实和快代理的写法一致）"""

    proxy_url: str
    username: str
    password: str
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        s.crawler = crawler
        return s

    def spider_opened(self, spider: AyuSpider) -> None:
        spider.slog.info(
            f"阿布云动态隧道代理中间件: AbuDynamicProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}"
        )
        dynamic_proxy_conf = self.crawler.settings.get("DYNAMIC_PROXY_CONFIG", None)
        # 查看动态隧道代理配置是否符合要求
        is_match = ReuseOperation.is_dict_meet_min_limit(
            data=dynamic_proxy_conf,
            keys={"proxy", "username", "password"},
        )
        assert is_match, (
            f"没有配置动态隧道代理，配置示例为：{Param.dynamic_proxy_conf_example}"
        )

        self.proxy_url = dynamic_proxy_conf["proxy"]
        self.username = dynamic_proxy_conf["username"]
        self.password = dynamic_proxy_conf["password"]

    def process_request(self, request: Request) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        if request.url.startswith("https://"):
            request.meta["proxy"] = f"https://{self.proxy_url}"
        elif request.url.startswith("http://"):
            request.meta["proxy"] = f"http://{self.proxy_url}"
        else:
            spider.slog.info(f"request url error: {request.url}")

        proxy_user_pass = f"{self.username}:{self.password}"
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(
            bytes(proxy_user_pass, "ascii")
        ).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass
