from __future__ import annotations

import base64
import json
import urllib.request
from typing import TYPE_CHECKING

from scrapy import signals

__all__ = [
    "ExclusiveProxyDownloaderMiddleware",
]

if TYPE_CHECKING:
    from scrapy import Request
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class ExclusiveProxyDownloaderMiddleware:
    """独享代理中间件"""

    def __init__(self):
        self.proxy_url = None
        self.username = None
        self.password = None
        self.proxy_index = None
        # 从 proxy_list 中取出索引为 proxy_index 的值
        self.proxy = None

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def get_proxy_ip(self, proxy_url: str, index: int) -> str:
        """获取独享代理接口的索引为 proxy_index 的代理信息"""
        try:
            r = urllib.request.urlopen(url=proxy_url)
            content = r.read().decode(errors="ignore")
            proxy_list = json.loads(content).get("data").get("proxy_list")
            proxy_list.sort()
            if index < len(proxy_list):
                return proxy_list[index]
            else:
                raise IndexError("独享代理取值索引超出范围，请确认独享代理服务情况。")

        except Exception:
            raise Exception("获取独享代理时失败，请查看独享配置及网络是否正常。")

    def process_request(self, request: Request, spider: AyuSpider) -> None:
        if request.url.startswith("https://"):
            request.meta["proxy"] = f"https://{self.proxy}"
        elif request.url.startswith("http://"):
            request.meta["proxy"] = f"http://{self.proxy}"
        else:
            spider.slog.info(f"request url error: {request.url}")

        proxy_user_pass = f"{self.username}:{self.password}"
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(
            bytes(proxy_user_pass, "ascii")
        ).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass

    def spider_opened(self, spider: AyuSpider) -> None:
        spider.slog.info(
            f"独享代理中间件: ExclusiveProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}"
        )

        self.proxy_url = spider.exclusiveproxy_conf.proxy
        self.username = spider.exclusiveproxy_conf.username
        self.password = spider.exclusiveproxy_conf.password
        self.proxy_index = spider.exclusiveproxy_conf.index
        self.proxy = self.get_proxy_ip(proxy_url=self.proxy_url, index=self.proxy_index)
