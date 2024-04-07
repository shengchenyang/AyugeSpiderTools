import asyncio
from typing import TYPE_CHECKING, Any, Optional, Tuple, TypeVar, Union

import aiohttp
from itemadapter import ItemAdapter
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.utils.python import global_object_name

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.common.typevars import AiohttpConf, AiohttpRequestArgs
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.config import logger

__all__ = [
    "AiohttpDownloaderMiddleware",
]

if TYPE_CHECKING:
    from scrapy import Request
    from scrapy.crawler import Crawler
    from scrapy.http import Response
    from scrapy.statscollectors import StatsCollector
    from typing_extensions import Self

    from ayugespidertools.common.typevars import slogT
    from ayugespidertools.scraper.http import AiohttpRequest
    from ayugespidertools.spiders import AyuSpider

    AyuRequest = Union[AiohttpRequest, Request]

ItemAdapterT = TypeVar("ItemAdapterT", bound=ItemAdapter)


class AiohttpDownloaderMiddleware:
    """Downloader middleware handling the requests with aiohttp"""

    session: "aiohttp.ClientSession"
    priority_adjust: int
    aiohttp_cfg: AiohttpConf
    aiohttp_args: dict
    slog: "slogT"

    def _retry(
        self,
        request: "AyuRequest",
        reason: int,
        spider: "AyuSpider",
    ) -> Optional["AyuRequest"]:
        """重试请求

        Args:
            request: retry request
            reason: retry reason
            spider: AyuSpider

        Returns:
            1). Optional["AyuRequest"]: 重试的 request 对象
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
        request: "AyuRequest",
        retries: int,
        reason: int,
        stats: "StatsCollector",
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

    def _get_args(self, key: str) -> Any:
        """根据优先级依次获取不为 None 的请求参数"""
        data_lst = [
            self.aiohttp_args.get(key),
            getattr(self.aiohttp_cfg, key),
        ]
        return ToolsForAyu.first_not_none(data_lst=data_lst)

    def spider_opened(self, spider: "AyuSpider") -> None:
        self.slog = spider.slog
        settings = spider.crawler.settings
        # 自定义 aiohttp 全局配置信息，优先级小于 aiohttp_meta 中的配置
        if local_aiohttp_conf := settings.get("AIOHTTP_CONFIG", {}):
            # 这里的配置信息如果在 aiohttp_meta 中重复设置，则会更新当前请求的参数
            self.aiohttp_cfg = AiohttpConf(
                timeout=settings.get("DOWNLOAD_TIMEOUT"),
                sleep=local_aiohttp_conf.get("sleep"),
                proxy=local_aiohttp_conf.get("proxy"),
                proxy_auth=local_aiohttp_conf.get("proxy_auth"),
                proxy_headers=local_aiohttp_conf.get("proxy_headers"),
                retry_times=local_aiohttp_conf.get(
                    "retry_times", Param.aiohttp_retry_times_default
                ),
                limit=local_aiohttp_conf.get("limit", 100),
                ssl=local_aiohttp_conf.get("ssl", True),
                verify_ssl=local_aiohttp_conf.get("verify_ssl", True),
                limit_per_host=local_aiohttp_conf.get("limit_per_host", 0),
                allow_redirects=local_aiohttp_conf.get("allow_redirects", True),
            )

            # 这些参数全局生效，不会在 meta 中更新
            _connector = aiohttp.TCPConnector(
                ssl=self.aiohttp_cfg.ssl,
                limit=self.aiohttp_cfg.limit,
                verify_ssl=self.aiohttp_cfg.verify_ssl,
                limit_per_host=self.aiohttp_cfg.limit_per_host,
            )
            # 超时设置, 若同时配置 AiohttpRequestArgs 的 timeout 参数会更新此值
            _timeout = aiohttp.ClientTimeout(total=self.aiohttp_cfg.timeout)
            self.session = aiohttp.ClientSession(connector=_connector, timeout=_timeout)
            self.priority_adjust = settings.getint("RETRY_PRIORITY_ADJUST")

    @classmethod
    def from_crawler(cls, crawler: "Crawler") -> "Self":
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    async def _request_by_aiohttp(
        self,
        aio_request_args: ItemAdapterT,
    ) -> Tuple[int, str]:
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
        self, request: "AyuRequest", spider: "AyuSpider"
    ) -> Union["AyuRequest", "Response", None]:
        aiohttp_options = request.meta.get("aiohttp")
        self.aiohttp_args = aiohttp_options.setdefault("args", {})

        # 设置 url
        _url = self.aiohttp_args.get("url") or request.url
        aiohttp_req_args = AiohttpRequestArgs(url=_url)

        # 设置请求方式
        if _method := self.aiohttp_args.get("method"):
            aiohttp_req_args.method = _method
        elif _method := str(request.method).upper():
            aiohttp_req_args.method = _method  # type: ignore
        if _method not in {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}:
            logger.error(f"出现未知请求方式 {_method}，请及时查看，默认 GET")

        # 设置请求头信息
        if _headers_args := self.aiohttp_args.get("headers"):
            aiohttp_req_args.headers = _headers_args
        elif _headers_args := ToolsForAyu.get_dict_form_scrapy_req_headers(
            scrapy_headers=request.headers
        ):
            aiohttp_req_args.headers = _headers_args

        # 设置请求 body 参数，GET 情况下和 POST 情况下的请求参数处理
        if _req_data := self.aiohttp_args.get("data"):
            aiohttp_req_args.data = _req_data
        elif req_data_str := str(request.body, encoding="utf-8"):
            # 如果是 json 字典格式的数据时，则是 scrapy body 传来的 json dumps 参数
            if ReuseOperation.judge_str_is_json(judge_str=req_data_str):
                aiohttp_req_args.data = req_data_str
            # 否则就是传来的字典格式
            else:
                req_data_dict = ReuseOperation.get_req_dict_from_scrapy(
                    req_body_data_str=req_data_str
                )
                aiohttp_req_args.data = req_data_dict

        # 设置 proxy
        if _proxy := self._get_args("proxy"):
            aiohttp_req_args.proxy = _proxy
        if _proxy_auth := self._get_args("proxy_auth"):
            aiohttp_req_args.proxy_auth = _proxy_auth
        if _proxy_headers := self._get_args("proxy_headers"):
            aiohttp_req_args.proxy_headers = _proxy_headers

        # 设置 allow_redirects
        _allow_redirects = self._get_args("allow_redirects")
        if _allow_redirects is not None:
            aiohttp_req_args.allow_redirects = _allow_redirects

        # 设置 cookies，优先从 AiohttpRequest 中的 cookies 参数中取值，没有时再从 headers 中取值
        _ck_args = self.aiohttp_args.get("cookies")
        aiohttp_cookie_dict = _ck_args if _ck_args is not None else request.cookies
        if all([not aiohttp_cookie_dict, request.headers.get("Cookie", None)]):
            headers_cookie_str = str(request.headers.get("Cookie"), encoding="utf-8")
            aiohttp_cookie_dict = ReuseOperation.get_ck_dict_from_headers(
                headers_ck_str=headers_cookie_str
            )
        aiohttp_req_args.cookies = aiohttp_cookie_dict

        # 超时设置
        if _timeout := self.aiohttp_args.get("timeout"):
            aiohttp_req_args.timeout = _timeout

        aio_request_args = ItemAdapter(aiohttp_req_args)
        status_code, html_content = await self._request_by_aiohttp(
            aio_request_args=aio_request_args
        )

        # 请求间隔设置
        _sleep = self._get_args("sleep")
        await asyncio.sleep(_sleep)

        if all([status_code == 504, not html_content]):
            spider.slog.error(f"url: {_url} 返回内容为空，请求超时！")
            self._retry(request=request, reason=504, spider=spider)

        return HtmlResponse(
            url=_url,
            status=status_code,
            headers=aiohttp_req_args.headers,
            body=html_content,
            encoding="utf-8",
            request=request,
        )

    async def spider_closed(self, spider: "AyuSpider") -> None:
        await self.session.close()
