from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import aiohttp
from scrapy import signals
from scrapy.http import Headers, HtmlResponse
from scrapy.responsetypes import responsetypes
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
    from ayugespidertools.scraper.http.request.aiohttp import AiohttpRequest
    from ayugespidertools.spiders import AyuSpider

    AyuRequest = AiohttpRequest | Request


AIOHTTP_REQUEST_ERROR_STATUS = 599
AIOHTTP_DECODED_RESPONSE_HEADERS = (b"Content-Encoding", b"Content-Length")


class AiohttpDownloaderMiddleware:
    """Downloader middleware handling the requests with aiohttp"""

    session: aiohttp.ClientSession
    priority_adjust: int
    aiohttp_cfg: AiohttpConf
    aiohttp_args: dict
    slog: slogT
    crawler: Crawler

    def _retry(
        self, request: AyuRequest, reason: str | int | Exception, spider: AyuSpider
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
        reason: str | int | Exception,
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
        s.crawler = crawler
        return s

    @staticmethod
    def _response_headers_from_aiohttp(
        response: aiohttp.ClientResponse, auto_decompress: bool
    ) -> Headers:
        headers = Headers(response.raw_headers)
        if auto_decompress and b"Content-Encoding" in headers:
            for header in AIOHTTP_DECODED_RESPONSE_HEADERS:
                headers.pop(header, None)
        return headers

    async def _request_by_aiohttp(
        self, aio_request_args: ItemAdapter | dict
    ) -> tuple[int, str, Headers, bytes]:
        """使用 aiohttp 来请求

        Args:
            aio_request_args: aiohttp 请求参数

        Returns:
            1). response_status: 响应状态码
            2). response_url: 响应 URL
            3). response_headers: 响应头
            4). response_body: 响应内容
        """
        async with self.session.request(**aio_request_args) as response:
            response_status = response.status
            response_url = str(response.url)
            response_headers = self._response_headers_from_aiohttp(
                response=response,
                auto_decompress=aio_request_args.get("auto_decompress") is not False,
            )
            response_body = await response.read()
            return response_status, response_url, response_headers, response_body

    @staticmethod
    def _response_status_from_error(error: Exception) -> int:
        return getattr(error, "status", None) or AIOHTTP_REQUEST_ERROR_STATUS

    async def process_request(
        self, request: AyuRequest
    ) -> AyuRequest | Response | None:
        spider = cast("AyuSpider", self.crawler.spider)
        aiohttp_options = request.meta.get("aiohttp", {})
        self.aiohttp_args = aiohttp_options.setdefault("args", {})
        aiohttp_req_args = ReuseOperation.filter_none_value(data=self.aiohttp_args)

        try:
            (
                response_status,
                response_url,
                response_headers,
                response_body,
            ) = await self._request_by_aiohttp(aio_request_args=aiohttp_req_args)
        except Exception as e:
            self.slog.error(f"url: {request.url} aiohttp 请求失败，Error: {e}")
            response_status = self._response_status_from_error(e)

            if _sleep := self.aiohttp_cfg.sleep:
                await asyncio.sleep(_sleep)

            retry_req = self._retry(request=request, reason=e, spider=spider)
            if retry_req is not None:
                return retry_req

            return HtmlResponse(
                url=request.url,
                status=response_status,
                headers=request.headers,
                body=b"",
                encoding="utf-8",
                request=request,
            )

        if _sleep := self.aiohttp_cfg.sleep:
            await asyncio.sleep(_sleep)

        response_class = responsetypes.from_args(
            headers=response_headers,
            url=response_url,
            body=response_body,
        )

        return response_class(
            url=response_url,
            status=response_status,
            headers=response_headers,
            body=response_body,
            request=request,
        )

    async def spider_closed(self, spider: AyuSpider) -> None:
        await self.session.close()
