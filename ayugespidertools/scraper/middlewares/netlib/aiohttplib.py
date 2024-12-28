from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Union

import aiohttp
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.utils.python import global_object_name

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.common.typevars import AiohttpConf
from ayugespidertools.config import logger

__all__ = [
    "AiohttpDownloaderMiddleware",
]

if TYPE_CHECKING:
    from itemadapter import ItemAdapter
    from scrapy import Request
    from scrapy.crawler import Crawler
    from scrapy.http import Response
    from scrapy.statscollectors import StatsCollector
    from typing_extensions import Self

    from ayugespidertools.common.typevars import slogT
    from ayugespidertools.scraper.http import AiohttpRequest
    from ayugespidertools.spiders import AyuSpider

    AyuRequest = Union[AiohttpRequest, Request]


class AiohttpDownloaderMiddleware:
    """Downloader middleware handling the requests with aiohttp"""

    session: aiohttp.ClientSession
    priority_adjust: int
    aiohttp_cfg: AiohttpConf
    aiohttp_args: dict
    slog: slogT

    def _retry(
        self,
        request: AyuRequest,
        reason: str | int,
        spider: AyuSpider,
    ) -> AyuRequest | None:
        """重试请求

        Args:
            request: retry request
            reason: retry reason
            spider: AyuSpider

        Returns:
            1). AyuRequest | None: 重试的 request 对象
        """
        retries = request.meta.get("retry_times", 0) + 1
        stats = spider.crawler.stats
        if retries <= self.aiohttp_cfg.retry_times:
            return self._retry_with_limit(request, retries, reason, stats)

        stats.inc_value("retry/max_reached")
        logger.error(f"Gave up retrying {request} (failed {retries} times): {reason}")
        return None

    def _retry_with_limit(
        self,
        request: AyuRequest,
        retries: int,
        reason: str | int,
        stats: StatsCollector,
    ):
        logger.debug(f"Retrying {request} (failed {retries} times): {reason}")
        retry_req = request.copy()
        retry_req.meta["retry_times"] = retries
        retry_req.dont_filter = True
        # 优先级逐级降低，以防堆积
        retry_req.priority = request.priority + self.priority_adjust

        if isinstance(reason, Exception):
            reason = global_object_name(reason.__class__)

        stats.inc_value("retry/count")
        stats.inc_value(f"retry/reason_count/{reason}")
        return retry_req

    async def spider_opened(self, spider: AyuSpider) -> None:
        self.slog = spider.slog
        settings = spider.crawler.settings
        # 自定义 aiohttp 全局配置信息，优先级小于 aiohttp_meta 中的配置
        if _aiohttp_cfg := settings.get("AIOHTTP_CONFIG", {}):
            # 这里的配置信息如果在 aiohttp_meta 中重复设置，则会更新当前请求的参数
            self.aiohttp_cfg = AiohttpConf(
                # 设置 aiohttp.TCPConnector 中的配置
                verify_ssl=_aiohttp_cfg.get("verify_ssl"),
                fingerprint=_aiohttp_cfg.get("fingerprint"),
                use_dns_cache=_aiohttp_cfg.get("use_dns_cache"),
                ttl_dns_cache=_aiohttp_cfg.get("ttl_dns_cache"),
                family=_aiohttp_cfg.get("family"),
                ssl_context=_aiohttp_cfg.get("ssl_context"),
                ssl=_aiohttp_cfg.get("ssl"),
                local_addr=_aiohttp_cfg.get("local_addr"),
                resolver=_aiohttp_cfg.get("resolver"),
                keepalive_timeout=_aiohttp_cfg.get("keepalive_timeout"),
                force_close=_aiohttp_cfg.get("force_close"),
                limit=_aiohttp_cfg.get("limit"),
                limit_per_host=_aiohttp_cfg.get("limit_per_host"),
                enable_cleanup_closed=_aiohttp_cfg.get("enable_cleanup_closed"),
                loop=_aiohttp_cfg.get("loop"),
                timeout_ceil_threshold=_aiohttp_cfg.get("timeout_ceil_threshold"),
                happy_eyeballs_delay=_aiohttp_cfg.get("happy_eyeballs_delay"),
                interleave=_aiohttp_cfg.get("interleave"),
                # 设置一些自定义的全局参数
                timeout=settings.get("DOWNLOAD_TIMEOUT"),
                sleep=_aiohttp_cfg.get("sleep"),
                retry_times=_aiohttp_cfg.get(
                    "retry_times", Param.aiohttp_retry_times_default
                ),
            )

            aiohttp_tcp_conn = ReuseOperation.get_items_except_keys(
                data=self.aiohttp_cfg._asdict(),
                keys={"timeout", "sleep", "retry_times"},
            )
            aiohttp_tcp_conn_args = ReuseOperation.filter_none_value(aiohttp_tcp_conn)
            _connector = aiohttp.TCPConnector(**aiohttp_tcp_conn_args)
            # 超时设置, 若同时配置 AiohttpRequestArgs 的 timeout 参数会更新此值
            _timeout = aiohttp.ClientTimeout(total=self.aiohttp_cfg.timeout)
            self.session = aiohttp.ClientSession(connector=_connector, timeout=_timeout)
            self.priority_adjust = settings.getint("RETRY_PRIORITY_ADJUST")

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    async def _request_by_aiohttp(
        self,
        aio_request_args: ItemAdapter | dict,
    ) -> tuple[int, str]:
        """使用 aiohttp 来请求

        Args:
            aio_request_args: aiohttp 请求参数

        Returns:
            1). status_code: 状态码
            2). r_text: 响应内容
        """
        try:
            async with self.session.request(**aio_request_args) as r:
                status_code = r.status
                r_text = await r.text(errors="ignore")
                return status_code, r_text
        except Exception as e:
            self.slog.error(f"aiohttp 出现请求错误，Error: {e}")
            return 504, ""

    async def process_request(
        self, request: AyuRequest, spider: AyuSpider
    ) -> AyuRequest | Response | None:
        aiohttp_options = request.meta.get("aiohttp")
        self.aiohttp_args = aiohttp_options.setdefault("args", {})

        # 设置 aiohttp 请求参数
        aiohttp_req_args = ReuseOperation.filter_none_value(data=self.aiohttp_args)
        status_code, html_content = await self._request_by_aiohttp(
            aio_request_args=aiohttp_req_args
        )

        # 请求间隔设置
        if _sleep := self.aiohttp_cfg.sleep:
            await asyncio.sleep(_sleep)

        # 重试请求
        if all([status_code == 504, not html_content]):
            spider.slog.error(f"url: {request.url} 返回内容为空，请求超时！")
            self._retry(request=request, reason=504, spider=spider)

        return HtmlResponse(
            url=request.url,
            status=status_code,
            headers=request.headers,
            body=html_content,
            encoding="utf-8",
            request=request,
        )

    async def spider_closed(self, spider: AyuSpider) -> None:
        await self.session.close()
