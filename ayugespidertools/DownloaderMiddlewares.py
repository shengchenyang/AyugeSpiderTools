#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  DownloaderMiddlewares.py
@Time    :  2022/8/30 16:36
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import asyncio
import aiohttp
import urllib.parse
from loguru import logger
from scrapy.http import HtmlResponse
from twisted.internet.defer import Deferred
from ayugespidertools.common.Params import Param
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.common.MultiPlexing import ReuseOperation


__all__ = [
    "AiohttpMiddleware",
    "AiohttpAsyncMiddleware",
]


def as_deferred(f):
    """
    transform a Twisted Deffered to an Asyncio Future
    Args:
        f: async function

    Returns:
        1).Deferred
    """
    return Deferred.fromFuture(asyncio.ensure_future(f))


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
        local_aiohttp_conf = settings.get("LOCAL_AIOHTTP_CONFIG", {})

        # 这里的配置信息如果在 aiohttp_meta 中重复设置，则会更新当前请求的参数
        if ReuseOperation.if_dict_meet_min_limit(dict_config=local_aiohttp_conf, key_list=["TIMEOUT", "RETRY_TIMES"]):
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
            # 用来标记是否在配置中设置
            cls.aio_local_conf_exists = True

        else:
            logger.warning(f"aiohttp 运行缺少最低配置内容要求，示例为：{Param.aiohttp_conf_example}，现尝试从 aiohttp_args 中获取！")

        cls.aio_local_conf_exists = False
        return cls()

    async def _request_by_aiohttp(self, aio_request_args: dict, aio_request_cookies: dict) -> str:
        async with aiohttp.ClientSession(cookies=aio_request_cookies) as session:
            async with session.request(**aio_request_args) as response:
                # logger.info(f"Status: {response.status}")
                # logger.info(f"Content-type: {response.headers['content-type']}")
                html = await response.text()
                return html

    async def _process_request(self, request, spider):
        """
        使用 aiohttp 来 process spider
        """
        aiohttp_meta = request.meta.get('aiohttp_args', {})
        if not isinstance(aiohttp_meta, dict):
            raise Exception("aiohttp_args 参数的格式不是 dict，请查看！")

        # set proxy

        # set cookies domain 参数
        parse_result = urllib.parse.urlsplit(request.url)
        domain = parse_result.hostname

        # _timeout = self.download_timeout
        # if aiohttp_meta.get('timeout') is not None:
        #     _timeout = aiohttp_meta.get('timeout')

        # logger.debug(f'crawling {request.url}')
        html_content = None
        try:
            # 获取请求头信息
            aiohttp_headers = ToolsForAyu.get_dict_form_scrapy_req_headers(scrapy_headers=request.headers)
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
                logger.warning(f"出现未知请求方式，请及时查看，默认 GET")
                aiohttp_args_dict = default_aiohttp_args_dict

            # 设置请求 body 参数，GET 情况下和 POST 情况下的请求参数处理
            request_body_str = str(request.body, encoding="utf-8")

            if request_body_str:
                # 如果是 json 字典格式的数据时，则是 scrapy body 传来的 json dumps 参数
                if ReuseOperation.judge_str_is_json(judge_str=request_body_str):
                    aiohttp_args_dict["data"] = request_body_str

                # 否则就是传来的字典格式
                else:
                    req_body_dict = ReuseOperation.get_req_dict_from_scrapy(req_body_data_str=request_body_str)
                    aiohttp_args_dict["data"] = req_body_dict

            # 如果存在请求头，则设置此请求头
            if aiohttp_headers:
                aiohttp_args_dict.update(aiohttp_headers_args)

            # 设置 cookies，优先从 AiohttpRequest 中的 cookies 参数中取值，没有时再从 headers 中取值
            aiohttp_cookie_dict = request.cookies
            # logger.debug(f"使用 cookies 参数中 ck 的值: {aiohttp_cookie_dict}")
            if all([not aiohttp_cookie_dict, request.headers.get("Cookie", None)]):
                headers_cookie_str = str(request.headers.get("Cookie"), encoding="utf-8")
                aiohttp_cookie_dict = ReuseOperation.get_ck_dict_from_headers(headers_ck_str=headers_cookie_str)
                # logger.debug(f"使用 headers 中 ck 的值: {aiohttp_cookie_dict}, {type(aiohttp_cookie_dict)}")

            html_content = await self._request_by_aiohttp(
                aio_request_args=aiohttp_args_dict,
                aio_request_cookies=aiohttp_cookie_dict)

        except TimeoutError:
            logger.exception(f'使用 aiohttp 错误响应 url: {request.url}')
            # return self._retry(request, 504, spider)

        # 休眠或延迟设置
        # if not self.sleep:
        if not self.aio_local_conf_exists:
            self.timeout = aiohttp_meta.get("timeout", Param.aiohttp_timeout_default)
            self.sleep = aiohttp_meta.get("sleep", Param.aiohttp_sleep_default)
            self.retry_times = aiohttp_meta.get("retry_times", Param.aiohttp_retry_times_default)
        await asyncio.sleep(self.sleep)

        body = str.encode(html_content)
        if not html_content:
            logger.error(f'url: {request.url} 返回内容为空')

        response = HtmlResponse(
            request.url,
            status=200,
            # headers={"response_header_example": "tmp"},
            body=body,
            encoding='utf-8',
            request=request
        )
        return response

    def process_request(self, request, spider):
        """
        使用 aiohttp 来 process request
        Args:
            request: AiohttpRequest 对象
            spider: scrapy spider

        Returns:
            1). Deferred
        """
        return as_deferred(self._process_request(request, spider))

    async def _spider_closed(self):
        pass

    def spider_closed(self):
        """
        当 spider closed 时调用
        """
        return as_deferred(self._spider_closed())


class AiohttpAsyncMiddleware(AiohttpMiddleware):
    """aiohttp 协程的另一种实现方法，简化 process_request 方法"""

    async def process_request(self, request, spider):
        await super()._process_request(request, spider)
