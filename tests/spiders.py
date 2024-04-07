import json

from scrapy.http.response.text import TextResponse

from ayugespidertools import AiohttpFormRequest, AiohttpRequest
from ayugespidertools.common.typevars import AiohttpRequestArgs
from ayugespidertools.spiders import AyuSpider
from tests.conftest import article_list_table


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


class Operations:
    """项目依赖方法"""

    @staticmethod
    def parse_response_data(response_data: str, mark: str):
        """解析测试请求中的内容，并打印基本信息

        Args:
            response_data: 请求响应内容
            mark: 请求标识

        Returns:
            args: request args
            headers: request headers
            origin: request origin
            url: request url
        """
        print(f"mark: {mark}, content: {response_data}")
        json_data = json.loads(response_data)
        args = json_data["args"]
        headers = json_data["headers"]
        origin = json_data["origin"]
        url = json_data["url"]
        print(f"{mark} response, args: {args}")
        print(f"{mark} response, headers: {headers}")
        print(f"{mark} response, origin: {origin}")
        print(f"{mark} response, url: {url}")
        return args, headers, origin, url


class DemoAiohttpSpider(SimpleSpider):
    name = "demo_aiohttp_example"
    allowed_domains = ["httpbin.org"]
    start_urls = ["http://httpbin.org/"]
    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOADER_MIDDLEWARES": {
            "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
            "ayugespidertools.middlewares.AiohttpDownloaderMiddleware": 543,
        },
        # scrapy Request 替换为 aiohttp 的配置示例
        "AIOHTTP_CONFIG": {
            # "proxy": "http://127.0.0.1:7890",
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
    _get_url = "http://httpbin.org/get?get_args=1"
    _ar_headers_ck = "headers_ck_key=ck; headers_ck_key2=ck"
    _ar_ck = {"ck_key": "ck"}
    _post_data = {"post_key1": "post_value1", "post_key2": "post_value2"}

    def start_requests(self):
        # GET normal 示例
        yield AiohttpRequest(
            url=self._get_url,
            callback=self.parse_get_fir,
            # aiohttp 的中间件下，headers 和 cookies 参数中的 ck 值不会冲突，但是当两参数中的 key 值一样时，库中默认取 cookies 中的值。
            # 所以此时，cookies 参数的优先级比较高
            headers={"Cookie": self._ar_headers_ck},
            cookies=self._ar_ck,
            meta={"meta_data": "get_normal"},
            cb_kwargs={"request_name": 1},
            dont_filter=True,
        )

        # GET with aiohttp args 示例
        yield AiohttpRequest(
            url=self._get_url,
            callback=self.parse_get_fir,
            meta={"meta_data": "get_with_aiohttp_args"},
            args=AiohttpRequestArgs(
                method="GET",
                headers={"Cookie": self._ar_headers_ck},
                cookies=self._ar_ck,
            ),
            cb_kwargs={"request_name": 2},
            dont_filter=True,
        )

        # POST normal 示例
        yield AiohttpRequest(
            url="http://httpbin.org/post",
            method="POST",
            callback=self.parse_post_fir,
            headers={"Cookie": self._ar_headers_ck},
            body=json.dumps(self._post_data),
            cookies=self._ar_ck,
            meta={"meta_data": "post_normal"},
            cb_kwargs={"request_name": 3},
            dont_filter=True,
        )

        # POST with aiohttp args 示例
        yield AiohttpRequest(
            url="http://httpbin.org/post",
            callback=self.parse_post_fir,
            args=AiohttpRequestArgs(
                method="POST",
                headers={"Cookie": self._ar_headers_ck},
                cookies=self._ar_ck,
                data=json.dumps(self._post_data),
            ),
            meta={"meta_data": "post_with_aiohttp_args"},
            cb_kwargs={"request_name": 4},
            dont_filter=True,
        )

        # POST(FormRequest) 示例
        yield AiohttpFormRequest(
            url="http://httpbin.org/post",
            headers={"Cookie": self._ar_headers_ck},
            cookies=self._ar_ck,
            formdata=self._post_data,
            callback=self.parse_post_sec,
            meta={"meta_data": "POST(FormRequest)"},
            cb_kwargs={"request_name": 5},
            dont_filter=True,
        )

        # POST(FormRequest) with aiohttp args 示例
        yield AiohttpFormRequest(
            url="http://httpbin.org/post",
            callback=self.parse_post_sec,
            args=AiohttpRequestArgs(
                method="POST",
                headers={"Cookie": self._ar_headers_ck},
                cookies=self._ar_ck,
                data=self._post_data,
            ),
            meta={"meta_data": "POST(FormRequest)_with_aiohttp_args"},
            cb_kwargs={"request_name": 6},
            dont_filter=True,
        )

    def parse_get_fir(self, response: TextResponse, request_name: int):
        aiohttp_arg = response.meta["aiohttp"]["args"]
        if request_name == 1:
            assert aiohttp_arg == {"url": self._get_url}
        if request_name == 2:
            assert aiohttp_arg == {
                "url": None,
                "headers": {"Cookie": self._ar_headers_ck},
                "cookies": self._ar_ck,
                "method": "GET",
                "timeout": None,
                "data": None,
                "proxy": None,
                "proxy_auth": None,
                "proxy_headers": None,
            }
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"get meta_data: {meta_data}")
        Operations.parse_response_data(response_data=response.text, mark="GET FIRST")

    def parse_post_fir(self, response: TextResponse, request_name: int):
        aiohttp_arg = response.meta["aiohttp"]["args"]
        if request_name == 3:
            assert aiohttp_arg == {"url": self._get_url}
        if request_name == 4:
            assert aiohttp_arg == {
                "url": None,
                "headers": {"Cookie": self._ar_headers_ck},
                "cookies": {"ck_key": "ck"},
                "method": "POST",
                "timeout": None,
                "data": json.dumps(self._post_data),
                "proxy": None,
                "proxy_auth": None,
                "proxy_headers": None,
            }
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"post first meta_data: {meta_data}")
        Operations.parse_response_data(response_data=response.text, mark="POST FIRST")

    def parse_post_sec(self, response: TextResponse, request_name: int):
        aiohttp_arg = response.meta["aiohttp"]["args"]
        if request_name == 5:
            assert aiohttp_arg == {"url": self._get_url}
        if request_name == 6:
            assert aiohttp_arg == {
                "url": None,
                "headers": {"Cookie": self._ar_headers_ck},
                "cookies": self._ar_ck,
                "method": "POST",
                "timeout": None,
                "data": self._post_data,
                "proxy": None,
                "proxy_auth": None,
                "proxy_headers": None,
            }

        meta_data = response.meta.get("meta_data")
        self.logger.info(f"post second meta_data: {meta_data}")
        Operations.parse_response_data(response_data=response.text, mark="POST SECOND")
