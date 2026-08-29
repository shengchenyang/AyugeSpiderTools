from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ayugespidertools import AiohttpRequest
from ayugespidertools.spiders import AyuSpider
from tests.conftest import article_list_table

if TYPE_CHECKING:
    from scrapy.http.response.text import TextResponse


class MockServerSpider(AyuSpider):
    def __init__(self, mockserver=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mockserver = mockserver


class MetaSpider(MockServerSpider):
    name = "meta"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.meta = {}

    def closed(self, reason):
        self.meta["close_reason"] = reason


class SimpleSpider(MetaSpider):
    name = "simple"

    def __init__(self, url="http://localhost:8998", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [url]

    def parse(self, response):
        self.logger.info(f"Got response {response.status}")


class RecordLogToMysqlSpider(SimpleSpider):
    name = "record_log_to_mysql"
    custom_settings = {
        "ITEM_PIPELINES": {
            "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
            "ayugespidertools.pipelines.AyuStatisticsMysqlPipeline": 301,
        },
        "DOWNLOADER_MIDDLEWARES": {
            "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
        },
    }

    def parse(self, response):
        yield {"_table": article_list_table, "data": "demo"}
        self.logger.info(f"Got response {response.status}")


class DemoAiohttpSpider(SimpleSpider):
    name = "demo_aiohttp_example"
    allowed_domains = ["postman-echo.com"]
    start_urls = ["https://postman-echo.com/"]
    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOADER_MIDDLEWARES": {
            "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
            "ayugespidertools.middlewares.AiohttpDownloaderMiddleware": 543,
        },
        # scrapy Request 替换为 aiohttp 的配置示例
        "AIOHTTP_CONFIG": {
            "sleep": 0,
            # 同时连接的总数
            "limit": 100,
            # 同时连接到一台主机的数量
            "limit_per_host": 0,
            "retry_times": 3,
            "ssl": False,
            # "verify_ssl": False,
            "allow_redirects": False,
        },
        "DOWNLOAD_TIMEOUT": 35,
    }

    # 这些参数用于测试临时使用
    _get_url = "https://postman-echo.com/get?get_args=1"
    _post_url = "https://postman-echo.com/post"
    _ar_headers_ck = "headers_ck_key=ck; headers_ck_key2=ck"
    _ar_ck = {"ck_key": "ck"}
    _post_data = {"post_key1": "post_value1", "post_key2": "post_value2"}

    async def start(self):
        # GET normal 示例
        yield AiohttpRequest(
            url=self._get_url,
            callback=self.parse_get_fir,
            headers={"Cookie": self._ar_headers_ck},
            cookies=self._ar_ck,
            meta={"meta_data": "get_normal"},
            cb_kwargs={"request_name": 1},
            dont_filter=True,
        )

        # POST normal 示例
        yield AiohttpRequest(
            url=self._post_url,
            method="POST",
            callback=self.parse_post_fir,
            headers={"Cookie": self._ar_headers_ck},
            cookies=self._ar_ck,
            meta={"meta_data": "post_normal"},
            cb_kwargs={"request_name": 3},
            dont_filter=True,
        )

    def parse_get_fir(self, response: TextResponse, request_name: int):
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"get meta_data: {meta_data}")
        json_data = json.loads(response.text)
        url = json_data.get("url")
        assert url == self._get_url

    def parse_post_fir(self, response: TextResponse, request_name: int):
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"post first meta_data: {meta_data}")
        json_data = json.loads(response.text)
        url = json_data.get("url")
        assert url == self._post_url
