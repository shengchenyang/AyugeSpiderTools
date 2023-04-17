import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from ayugespidertools import AioFormRequest, AiohttpRequest
from ayugespidertools.AyugeCrawlSpider import AyuCrawlSpider
from ayugespidertools.AyugeSpider import AyuSpider
from tests import PYMYSQL_CONFIG


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
        "RECORD_LOG_TO_MYSQL": True,
        "ITEM_PIPELINES": {
            "ayugespidertools.Pipelines.AyuFtyMysqlPipeline": 300,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # 随机请求头
            "ayugespidertools.Middlewares.RandomRequestUaMiddleware": 400,
        },
        "LOCAL_MYSQL_CONFIG": {
            "HOST": PYMYSQL_CONFIG["host"],
            "PORT": PYMYSQL_CONFIG["port"],
            "USER": PYMYSQL_CONFIG["user"],
            "PASSWORD": PYMYSQL_CONFIG["password"],
            "CHARSET": PYMYSQL_CONFIG["charset"],
            "DATABASE": PYMYSQL_CONFIG["database"],
        },
    }

    def parse(self, response):
        yield {"foo": 42}
        self.logger.info(f"Got response {response.status}")


class MyAyuCrawlSpider(AyuCrawlSpider):
    name = "My_AyuCrawlSpider"
    allowed_domains = ["zongheng.com"]
    start_urls = ["https://www.zongheng.com/rank/details.html?rt=1&d=1"]
    custom_settings = {
        "LOG_LEVEL": "DEBUG",
    }

    rules = (
        Rule(
            LinkExtractor(restrict_xpaths='//div[@class="rank_d_b_name"]/a'),
            callback="parse_item",
        ),
    )

    def parse_item(self, response):
        # 获取图书名称 - （获取的是详情页中的图书名称）
        book_name_list = response.xpath('//div[@class="book-name"]//text()').extract()
        book_name = "".join(book_name_list).strip()

        self.logger.info(f"book_name: {book_name}")


class Operations(object):
    """
    项目依赖方法
    """

    @staticmethod
    def parse_response_data(response_data: str, mark: str):
        """
        解析测试请求中的内容，并打印基本信息
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


class DemoAiohttpSpider(AyuSpider):
    name = "demo_aiohttp_example"
    allowed_domains = ["httpbin.org"]
    start_urls = ["http://httpbin.org/"]

    # 初始化配置的类型
    settings_type = "debug"
    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOADER_MIDDLEWARES": {
            # 随机请求头
            "ayugespidertools.Middlewares.RandomRequestUaMiddleware": 400,
            # 将 scrapy Request 替换为 aiohttp 方式
            "ayugespidertools.DownloaderMiddlewares.AiohttpMiddleware": 543,
            # 'ayugespidertools.DownloaderMiddlewares.AiohttpAsyncMiddleware': 543,
        },
        # scrapy Request 替换为 aiohttp 的配置示例
        "LOCAL_AIOHTTP_CONFIG": {
            "TIMEOUT": 5,
            "PROXY": "127.0.0.1:1080",
            "SLEEP": 0,
            "RETRY_TIMES": 3,
        },
    }

    def start_requests(self):
        """
        get 请求首页，获取项目列表数据
        """
        # 测试 GET 请求示例一
        yield AiohttpRequest(
            url="http://httpbin.org/get?get_args=1",
            callback=self.parse_get_fir,
            # aiohttp 的中间件下，headers 和 cookies 参数中的 ck 值不会冲突，但是当两参数中的 key 值一样时，库中默认取 cookies 中的值。
            # 所以此时，cookies 参数的优先级比较高
            headers={
                "Cookie": "headers_cookies_key1=headers_cookie_value1; test_key=test_headers_value"
            },
            cookies={
                "cookies_key1": "cookies_value1",
                "test_key": "test_cookies_value",
            },
            meta={
                "meta_data": "这是用来测试 parse_get_fir meta 的功能",
                "aiohttp_args": {
                    "timeout": 3,
                    "proxy": "这个功能暂不提供，后续添加",
                },
            },
            dont_filter=True,
        )

        # 测试 POST 请求示例一
        post_data = {"post_key1": "post_value1", "post_key2": "post_value2"}
        yield AiohttpRequest(
            url="http://httpbin.org/post",
            method="POST",
            callback=self.parse_post_fir,
            headers={
                "Cookie": "headers_cookies_key1=headers_cookie_value1; headers_cookies_key2=v2"
            },
            body=json.dumps(post_data),
            cookies={
                "cookies_key1": "cookies_value1",
            },
            meta={
                "meta_data": "这是用来测试 parse_post_fir meta 的功能",
                "aiohttp_args": {
                    "timeout": 3,
                    "proxy": "这个功能暂不提供，后续添加",
                },
            },
            dont_filter=True,
        )

        # 测试 POST 请求示例二
        yield AioFormRequest(
            url="http://httpbin.org/post",
            headers={"Cookie": "headers_cookies_key1=headers_cookie_value1;"},
            cookies={
                "cookies_key1": "cookies_value1",
            },
            formdata=post_data,
            callback=self.parse_post_sec,
            meta={
                "meta_data": "这是用来测试 parse_post_sec meta 的功能",
                "aiohttp_args": {
                    "timeout": 3,
                    "proxy": "这个功能暂不提供，后续添加",
                },
            },
            dont_filter=True,
        )

    def parse_get_fir(self, response):
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"get meta_data: {meta_data}")
        Operations.parse_response_data(response_data=response.text, mark="GET FIRST")

    def parse_post_fir(self, response):
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"post first meta_data: {meta_data}")
        Operations.parse_response_data(response_data=response.text, mark="POST FIRST")

    def parse_post_sec(self, response):
        meta_data = response.meta.get("meta_data")
        self.logger.info(f"post second meta_data: {meta_data}")
        Operations.parse_response_data(response_data=response.text, mark="POST SECOND")
