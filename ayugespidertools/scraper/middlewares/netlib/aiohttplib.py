import asyncio
from typing import Optional, Union

import aiohttp
import scrapy
from aiohttp.connector import BaseConnector
from scrapy.http import HtmlResponse
from scrapy.utils.python import global_object_name

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.common.typevars import AiohttpConfig, AiohttpRequestArgs
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.config import logger

__all__ = [
    "AiohttpDownloaderMiddleware",
    "AiohttpAsyncDownloaderMiddleware",
]


class AiohttpDownloaderMiddleware(object):
    """
    Downloader middleware handling the requests with aiohttp
    """

    def __init__(self):
        self.aiohttp_args = None

    def _retry(
        self,
        request: scrapy.Request,
        reason: int,
        spider: scrapy.Spider,
    ) -> Union[scrapy.Request, None]:
        """
        重试请求
        Args:
            request: scrapy request
            reason: reason
            spider: scrapy spider

        Returns:
            retryreq: 重试的 request 对象
        """
        retries = request.meta.get("retry_times", 0) + 1
        stats = spider.crawler.stats
        if retries <= self.retry_times:
            logger.debug(f"Retrying {request} (failed {retries} times): {reason}")
            retryreq = request.copy()
            retryreq.meta["retry_times"] = retries
            retryreq.dont_filter = True
            # 优先级逐级降低，以防堆积
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value("retry/count")
            stats.inc_value(f"retry/reason_count/{reason}")
            return retryreq
        else:
            stats.inc_value("retry/max_reached")
            logger.error(
                f"Gave up retrying {request} (failed {retries} times): {reason}"
            )

    def _get_args(self, key: str):
        """
        根据优先级依次获取不为 None 的请求参数
        """
        data_lst = [
            self.aiohttp_args.get(key),
            getattr(self, key),
        ]
        return ToolsForAyu.first_not_none(data_lst=data_lst)

    @classmethod
    def from_crawler(cls, crawler):
        """
        初始化 middleware
        """
        settings = crawler.settings
        # 自定义 aiohttp 全局配置信息，优先级小于 aiohttp_meta 中的配置
        if local_aiohttp_conf := settings.get("LOCAL_AIOHTTP_CONFIG", {}):
            # 这里的配置信息如果在 aiohttp_meta 中重复设置，则会更新当前请求的参数
            _aiohttp_conf = AiohttpConfig(
                timeout=local_aiohttp_conf.get("timeout"),
                sleep=local_aiohttp_conf.get("sleep"),
                proxy=local_aiohttp_conf.get("proxy"),
                proxy_auth=local_aiohttp_conf.get("proxy_auth"),
                proxy_headers=local_aiohttp_conf.get("proxy_headers"),
                retry_times=local_aiohttp_conf.get(
                    "retry_times", Param.aiohttp_retry_times_default
                ),
                limit=local_aiohttp_conf.get("limit"),
                ssl=local_aiohttp_conf.get("ssl"),
                verify_ssl=local_aiohttp_conf.get("verify_ssl"),
                limit_per_host=local_aiohttp_conf.get("limit_per_host"),
            )

            # 初始化所需要的参数信息，用于构建 aiohttp 请求信息
            # cls.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
            # cls.proxy = settings.get('PROXY')
            cls.timeout = _aiohttp_conf.timeout
            cls.proxy = _aiohttp_conf.proxy
            cls.proxy_auth = _aiohttp_conf.proxy_auth
            cls.proxy_headers = _aiohttp_conf.proxy_headers
            cls.sleep = _aiohttp_conf.sleep
            cls.retry_times = _aiohttp_conf.retry_times
            cls.limit = _aiohttp_conf.limit
            cls.ssl = _aiohttp_conf.ssl
            cls.verify_ssl = _aiohttp_conf.verify_ssl
            cls.limit_per_host = _aiohttp_conf.limit_per_host
            cls.priority_adjust = settings.getint("RETRY_PRIORITY_ADJUST")

        return cls()

    async def _request_by_aiohttp(
        self,
        aio_request_args: Param.ItemAdapterType,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        connector: Optional[BaseConnector] = None,
    ) -> (int, str):
        """
        使用 aiohttp 来请求
        ps: 后续考虑是否需要使用 aiohttp.ClientSession 来处理 cookies
        Args:
            aio_request_args: 普通的 aiohttp 请求参数
            timeout: aiohttp.ClientSession 的 timeout 参数
            connector: aiohttp connector 参数

        Returns:
            1). status_code: 请求状态码
            2). response_text: 请求返回的文本内容
        """
        try:
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                async with session.request(**aio_request_args) as response:
                    status_code = response.status
                    response_text = await response.text()
                    return status_code, response_text
        except aiohttp.ClientTimeout:
            return 504, ""

    async def _process_request(self, request, spider):
        """
        使用 aiohttp 来 process spider
        """
        aiohttp_options = request.meta.get("aiohttp")
        self.aiohttp_args = aiohttp_options.setdefault("args", {})

        # 根据 LOCAL_AIOHTTP_CONFIG 中设置 aiohttp 请求参数，这里的参数全局生效，不会在 meta 中更新
        _connector = aiohttp.TCPConnector(
            ssl=self.ssl,
            limit=self.limit,
            verify_ssl=self.verify_ssl,
            limit_per_host=self.limit_per_host,
        )

        # 设置 url
        _url = self.aiohttp_args.get("url") or request.url
        aiohttp_req_args = AiohttpRequestArgs(
            url=_url,
        )

        # 设置请求方式
        if _method := self.aiohttp_args.get("method"):
            aiohttp_req_args.method = _method
        elif _method := str(request.method).upper():
            aiohttp_req_args.method = _method
        if _method not in {"GET", "POST"}:
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
        if _proxy := self._get_args(key="proxy"):
            aiohttp_req_args.proxy = _proxy
        if _proxy_auth := self._get_args(key="proxy_auth"):
            aiohttp_req_args.proxy_auth = _proxy_auth
        if _proxy_headers := self._get_args(key="proxy_headers"):
            aiohttp_req_args.proxy_headers = _proxy_headers

        # 设置 cookies，优先从 AiohttpRequest 中的 cookies 参数中取值，没有时再从 headers 中取值
        _ck_args = self.aiohttp_args.get("cookies")
        aiohttp_cookie_dict = _ck_args if _ck_args is not None else request.cookies
        if all([not aiohttp_cookie_dict, request.headers.get("Cookie", None)]):
            headers_cookie_str = str(request.headers.get("Cookie"), encoding="utf-8")
            aiohttp_cookie_dict = ReuseOperation.get_ck_dict_from_headers(
                headers_ck_str=headers_cookie_str
            )
        aiohttp_req_args.cookies = aiohttp_cookie_dict

        # 请求超时设置
        _timeout_obj = None
        if _timeout := self.aiohttp_args.get("timeout"):
            aiohttp_req_args.timeout = _timeout
        elif self.timeout is not None:
            _timeout_obj = aiohttp.ClientTimeout(total=self.timeout)

        aio_request_args = ToolsForAyu.convert_items_to_dict(item=aiohttp_req_args)
        status_code, html_content = await self._request_by_aiohttp(
            timeout=_timeout_obj,
            aio_request_args=aio_request_args,
            connector=_connector,
        )

        # 请求间隔设置
        _sleep = self._get_args(key="sleep")
        await asyncio.sleep(_sleep)

        if all([status_code == 504, not html_content]):
            spider.slog.error(f"url: {_url} 返回内容为空，请求超时！")
            self._retry(request=request, reason=504, spider=spider)

        body = str.encode(html_content)
        return HtmlResponse(
            url=_url,
            status=status_code,
            headers=aiohttp_req_args.headers,
            body=body,
            encoding="utf-8",
            request=request,
        )

    def process_request(self, request, spider):
        """
        使用 aiohttp 来 process request
        Args:
            request: AiohttpRequest 对象
            spider: scrapy spider

        Returns:
            1). Deferred
        """
        return ReuseOperation.as_deferred(self._process_request(request, spider))

    async def _spider_closed(self):
        pass

    def spider_closed(self):
        """
        当 spider closed 时调用
        """
        return ReuseOperation.as_deferred(self._spider_closed())


class AiohttpAsyncDownloaderMiddleware(AiohttpDownloaderMiddleware):
    """aiohttp 协程的另一种实现方法，简化 process_request 方法"""

    async def process_request(self, request, spider):
        await super()._process_request(request, spider)
