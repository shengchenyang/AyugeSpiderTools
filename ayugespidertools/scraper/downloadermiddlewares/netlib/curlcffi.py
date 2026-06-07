from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from scrapy import signals
from scrapy.http import Headers, HtmlResponse
from scrapy.responsetypes import responsetypes
from scrapy.utils.python import global_object_name

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.config import logger

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    # pip install ayugespidertools[all]
    pass

__all__ = [
    "CurlCffiDownloaderMiddleware",
]

if TYPE_CHECKING:
    from scrapy import Request
    from scrapy.crawler import Crawler
    from scrapy.http import Response
    from scrapy.statscollectors import StatsCollector
    from typing_extensions import Self

    from ayugespidertools.common.typevars import slogT
    from ayugespidertools.scraper.http.request.curlcffi import CurlCffiRequest
    from ayugespidertools.spiders import AyuSpider

    AyuRequest = CurlCffiRequest | Request


CURL_CFFI_REQUEST_ERROR_STATUS = 599
CURL_CFFI_LOCAL_CONFIG_KEYS = {"sleep", "retry_times"}
CURL_CFFI_DECODED_RESPONSE_HEADERS = (b"Content-Encoding", b"Content-Length")


class CurlCffiConf(NamedTuple):
    loop: asyncio.AbstractEventLoop | None = None
    async_curl: Any = None
    max_clients: int | None = None
    headers: Any = None
    cookies: Any = None
    auth: tuple[str, str] | None = None
    proxies: dict[str, str] | None = None
    proxy: str | None = None
    proxy_auth: tuple[str, str] | None = None
    base_url: str | None = None
    params: dict[str, object] | None = None
    verify: bool | None = None
    timeout: float | tuple[float, float] | None = None
    trust_env: bool | None = None
    allow_redirects: bool | str | None = None
    max_redirects: int | None = None
    retry: Any = None
    impersonate: str | None = None
    ja3: str | None = None
    akamai: str | None = None
    perk: str | None = None
    extra_fp: Any = None
    default_headers: bool | None = None
    default_encoding: Any = None
    curl_options: dict[Any, Any] | None = None
    curl_infos: list[object] | None = None
    http_version: Any = None
    debug: bool | None = None
    interface: str | None = None
    cert: str | tuple[str, str] | None = None
    response_class: type[curl_requests.Response] | None = None
    discard_cookies: bool | None = None
    raise_for_status: bool | None = None
    sleep: int | float | None = None
    retry_times: int | None = None


class CurlCffiDownloaderMiddleware:
    """Downloader middleware handling requests with curl_cffi."""

    session: curl_requests.AsyncSession
    priority_adjust: int
    curl_cffi_cfg: CurlCffiConf
    curl_cffi_args: dict
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
        if retries <= self.curl_cffi_cfg.retry_times:
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
        # 自定义 curl_cffi 全局配置信息，优先级小于 curl_cffi_meta 中的配置
        _curl_cffi_cfg = settings.getdict("CURL_CFFI_CONFIG", {})
        retry_times = _curl_cffi_cfg.get("retry_times")
        self.curl_cffi_cfg = CurlCffiConf(
            loop=_curl_cffi_cfg.get("loop"),
            async_curl=_curl_cffi_cfg.get("async_curl"),
            max_clients=_curl_cffi_cfg.get("max_clients"),
            headers=_curl_cffi_cfg.get("headers"),
            cookies=_curl_cffi_cfg.get("cookies"),
            auth=_curl_cffi_cfg.get("auth"),
            proxies=_curl_cffi_cfg.get("proxies"),
            proxy=_curl_cffi_cfg.get("proxy"),
            proxy_auth=_curl_cffi_cfg.get("proxy_auth"),
            base_url=_curl_cffi_cfg.get("base_url"),
            params=_curl_cffi_cfg.get("params"),
            verify=_curl_cffi_cfg.get("verify"),
            timeout=_curl_cffi_cfg.get("timeout", settings.get("DOWNLOAD_TIMEOUT")),
            trust_env=_curl_cffi_cfg.get("trust_env"),
            allow_redirects=_curl_cffi_cfg.get("allow_redirects"),
            max_redirects=_curl_cffi_cfg.get("max_redirects"),
            retry=_curl_cffi_cfg.get("retry"),
            impersonate=_curl_cffi_cfg.get("impersonate"),
            ja3=_curl_cffi_cfg.get("ja3"),
            akamai=_curl_cffi_cfg.get("akamai"),
            perk=_curl_cffi_cfg.get("perk"),
            extra_fp=_curl_cffi_cfg.get("extra_fp"),
            default_headers=_curl_cffi_cfg.get("default_headers"),
            default_encoding=_curl_cffi_cfg.get("default_encoding"),
            curl_options=_curl_cffi_cfg.get("curl_options"),
            curl_infos=_curl_cffi_cfg.get("curl_infos"),
            http_version=_curl_cffi_cfg.get("http_version"),
            debug=_curl_cffi_cfg.get("debug"),
            interface=_curl_cffi_cfg.get("interface"),
            cert=_curl_cffi_cfg.get("cert"),
            response_class=_curl_cffi_cfg.get("response_class"),
            discard_cookies=_curl_cffi_cfg.get("discard_cookies"),
            raise_for_status=_curl_cffi_cfg.get("raise_for_status"),
            sleep=_curl_cffi_cfg.get("sleep"),
            retry_times=(
                Param.aiohttp_retry_times_default
                if retry_times is None
                else retry_times
            ),
        )

        curl_cffi_session = ReuseOperation.get_items_except_keys(
            data=self.curl_cffi_cfg._asdict(),
            keys=CURL_CFFI_LOCAL_CONFIG_KEYS,
        )
        curl_cffi_session_args = ReuseOperation.filter_none_value(curl_cffi_session)
        self.session = curl_requests.AsyncSession(**curl_cffi_session_args)
        self.priority_adjust = settings.getint("RETRY_PRIORITY_ADJUST")

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        s.crawler = crawler
        return s

    async def _request_by_curl_cffi(
        self, curl_cffi_request_args: dict
    ) -> curl_requests.Response:
        """使用 curl_cffi 来请求"""
        return await self.session.request(**curl_cffi_request_args)

    @staticmethod
    def _response_status_from_error(error: Exception) -> int:
        response = getattr(error, "response", None)
        response_status = getattr(response, "status_code", None)
        return (
            response_status
            or getattr(error, "status", None)
            or CURL_CFFI_REQUEST_ERROR_STATUS
        )

    @staticmethod
    def _response_headers_from_curl_cffi(response: curl_requests.Response) -> Headers:
        headers = Headers(response.headers.multi_items())
        if b"Content-Encoding" in headers:
            for header in CURL_CFFI_DECODED_RESPONSE_HEADERS:
                headers.pop(header, None)
        return headers

    async def process_request(
        self, request: AyuRequest
    ) -> AyuRequest | Response | None:
        curl_cffi_options = request.meta.get("curl_cffi")
        if curl_cffi_options is None:
            return None

        spider = cast("AyuSpider", self.crawler.spider)
        self.curl_cffi_args = curl_cffi_options.setdefault("args", {})
        curl_cffi_req_args = ReuseOperation.filter_none_value(data=self.curl_cffi_args)

        try:
            response = await self._request_by_curl_cffi(
                curl_cffi_request_args=curl_cffi_req_args
            )
        except Exception as e:
            self.slog.error(f"url: {request.url} curl_cffi 请求失败，Error: {e}")
            response_status = self._response_status_from_error(e)

            if _sleep := self.curl_cffi_cfg.sleep:
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

        if _sleep := self.curl_cffi_cfg.sleep:
            await asyncio.sleep(_sleep)

        response_url = response.url or request.url
        response_body = response.content
        response_headers = self._response_headers_from_curl_cffi(response)
        response_class = responsetypes.from_args(
            headers=response_headers,
            url=response_url,
            body=response_body,
        )

        return response_class(
            url=response_url,
            status=response.status_code,
            headers=response_headers,
            body=response_body,
            request=request,
        )

    async def spider_closed(self, spider: AyuSpider) -> None:
        if session := getattr(self, "session", None):
            await session.close()
