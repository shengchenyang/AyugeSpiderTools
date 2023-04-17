import asyncio

import aiohttp
from scrapy.http import HtmlResponse

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Params import Param
from ayugespidertools.common.Utils import ToolsForAyu

__all__ = [
    "AiohttpMiddleware",
    "AiohttpAsyncMiddleware",
]


class AiohttpMiddleware(object):
    """
    Downloader middleware handling the requests with aiohttp
    """

    def _retry(self, request, reason, spider):
        """
        TODO: 重试方法，后续添加
        """
        pass

    @classmethod
    def from_crawler(cls, crawler):
        """
        初始化 middleware
        """
        settings = crawler.settings
        # 自定义 aiohttp 全局配置信息，优先级小于 aiohttp_meta 中的配置
        if local_aiohttp_conf := settings.get("LOCAL_AIOHTTP_CONFIG", {}):
            # 这里的配置信息如果在 aiohttp_meta 中重复设置，则会更新当前请求的参数
            aiohttp_conf_temp = {
                "TIMEOUT": local_aiohttp_conf.get("TIMEOUT"),
                "SLEEP": local_aiohttp_conf.get("SLEEP"),
                "PROXY": local_aiohttp_conf.get("PROXY"),
                "RETRY_TIMES": local_aiohttp_conf.get("RETRY_TIMES"),
            }

            aiohttp_conf_lowered = ReuseOperation.dict_keys_to_lower(aiohttp_conf_temp)

            # 初始化所需要的参数信息，用于构建 aiohttp 请求信息
            # cls.download_timeout = settings.get('DOWNLOAD_TIMEOUT', settings.get('DOWNLOAD_TIMEOUT', 5))
            # cls.sleep = settings.get('SLEEP', 1)
            # cls.retry_enabled = settings.getbool('RETRY_ENABLED')
            # cls.max_retry_times = settings.getint('RETRY_TIMES')
            # cls.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
            # cls.proxy = settings.get('PROXY')
            cls.timeout = aiohttp_conf_lowered.get("timeout", None)
            cls.proxy = aiohttp_conf_lowered.get("proxy", None)
            cls.sleep = aiohttp_conf_lowered.get("sleep", None)
            cls.retry_times = aiohttp_conf_lowered.get("retry_times", None)

        return cls()

    async def _request_by_aiohttp(
        self, aio_request_args: dict, aio_request_cookies: dict
    ) -> str:
        async with aiohttp.ClientSession(cookies=aio_request_cookies) as session:
            async with session.request(**aio_request_args) as response:
                # (f"Status: {response.status}")
                # (f"Content-type: {response.headers['content-type']}")
                return await response.text()

    async def _process_request(self, request, spider):
        """
        使用 aiohttp 来 process spider
        """
        aiohttp_meta = request.meta.get("aiohttp_args", {})
        assert isinstance(aiohttp_meta, dict), "aiohttp_args 参数的格式不是 dict，请查看！"

        # set proxy

        # todo: 此部分中的 domain 参数暂时不使用，后续考虑是否需要
        # set cookies domain 参数
        # parse_result = urllib.parse.urlsplit(request.url)
        # domain = parse_result.hostname

        # _timeout = self.download_timeout
        # if aiohttp_meta.get('timeout') is not None:
        #     _timeout = aiohttp_meta.get('timeout')

        html_content = None
        try:
            # 获取请求头信息
            aiohttp_headers = ToolsForAyu.get_dict_form_scrapy_req_headers(
                scrapy_headers=request.headers
            )
            aiohttp_headers_args = {"headers": aiohttp_headers}

            # 确定请求方式
            scrapy_request_method = str(request.method).upper()
            # 默认请求方式为 get
            default_aiohttp_args_dict = {
                "method": "GET",
                "url": request.url,
            }
            if scrapy_request_method == "GET":
                aiohttp_args_dict = default_aiohttp_args_dict

            elif scrapy_request_method == "POST":
                aiohttp_args_dict = {
                    "method": "POST",
                    "url": request.url,
                }

            else:
                spider.slog.warning("出现未知请求方式，请及时查看，默认 GET")
                aiohttp_args_dict = default_aiohttp_args_dict

            # 设置请求 body 参数，GET 情况下和 POST 情况下的请求参数处理
            if request_body_str := str(request.body, encoding="utf-8"):
                # 如果是 json 字典格式的数据时，则是 scrapy body 传来的 json dumps 参数
                if ReuseOperation.judge_str_is_json(judge_str=request_body_str):
                    aiohttp_args_dict["data"] = request_body_str

                # 否则就是传来的字典格式
                else:
                    req_body_dict = ReuseOperation.get_req_dict_from_scrapy(
                        req_body_data_str=request_body_str
                    )
                    aiohttp_args_dict["data"] = req_body_dict

            # 如果存在请求头，则设置此请求头
            if aiohttp_headers:
                aiohttp_args_dict.update(aiohttp_headers_args)

            # 设置 cookies，优先从 AiohttpRequest 中的 cookies 参数中取值，没有时再从 headers 中取值
            aiohttp_cookie_dict = request.cookies
            # spider.slog.info(f"使用 cookies 参数中 ck 的值: {aiohttp_cookie_dict}")
            if all([not aiohttp_cookie_dict, request.headers.get("Cookie", None)]):
                headers_cookie_str = str(
                    request.headers.get("Cookie"), encoding="utf-8"
                )
                aiohttp_cookie_dict = ReuseOperation.get_ck_dict_from_headers(
                    headers_ck_str=headers_cookie_str
                )
                # spider.slog.info(f"使用 headers 中 ck 的值: {aiohttp_cookie_dict}, {type(aiohttp_cookie_dict)}")

            html_content = await self._request_by_aiohttp(
                aio_request_args=aiohttp_args_dict,
                aio_request_cookies=aiohttp_cookie_dict,
            )

        except TimeoutError:
            spider.slog.error(f"使用 aiohttp 错误响应 url: {request.url}")
            # return self._retry(request, 504, spider)

        # 休眠或延迟设置(优先级顺序：scrapy meta 中的参数值 > settings 中的参数值 > default 自定义的参数值)
        self.timeout = (
            aiohttp_meta.get("timeout") or self.timeout or Param.aiohttp_timeout_default
        )
        self.sleep = (
            aiohttp_meta.get("sleep") or self.sleep or Param.aiohttp_sleep_default
        )
        self.retry_times = (
            aiohttp_meta.get("retry_times")
            or self.retry_times
            or Param.aiohttp_retry_times_default
        )
        await asyncio.sleep(self.sleep)

        body = str.encode(html_content)
        if not html_content:
            spider.slog.error(f"url: {request.url} 返回内容为空")

        return HtmlResponse(
            request.url,
            status=200,
            # headers={"response_header_example": "tmp"},
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


class AiohttpAsyncMiddleware(AiohttpMiddleware):
    """aiohttp 协程的另一种实现方法，简化 process_request 方法"""

    async def process_request(self, request, spider):
        await super()._process_request(request, spider)
