import base64

from scrapy import signals

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Params import Param


class DynamicProxyDownloaderMiddleware(object):
    """
    动态隧道代理中间件
    """

    def __init__(self, settings):
        """
        从 scrapy 配置中取出动态隧道代理的信息
        """
        dynamic_proxy_config = settings.get("DYNAMIC_PROXY_CONFIG", None)
        # 查看动态隧道代理配置是否符合要求
        is_match = ReuseOperation.if_dict_meet_min_limit(
            dict_config=dynamic_proxy_config,
            key_list=["PROXY_URL", "USERNAME", "PASSWORD"],
        )
        assert is_match, f"没有配置动态隧道代理，配置示例为：{Param.dynamic_proxy_config_example}"

        self.proxy_url = dynamic_proxy_config["PROXY_URL"]
        self.username = dynamic_proxy_config["USERNAME"]
        self.password = dynamic_proxy_config["PASSWORD"]

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # TODO: 根据权重来随机获取一个账号 DYNAMIC_PROXY_CONFIG
        # account = ReuseOperation.random_weight(self.account_arr)
        if request.url.startswith("https://"):
            request.meta[
                "proxy"
            ] = f"https://{self.username}:{self.password}@{self.proxy_url}/"
        elif request.url.startswith("http://"):
            request.meta[
                "proxy"
            ] = f"http://{self.username}:{self.password}@{self.proxy_url}/"
        else:
            spider.slog.info(
                f"request url: {request.url} error when use proxy middlewares!"
            )

        # 避免因连接复用导致隧道不能切换 IP
        request.headers["Connection"] = "close"
        # 采用 gzip 压缩加速访问
        request.headers["Accept-Encoding"] = "gzip"

    def spider_opened(self, spider):
        spider.slog.info(
            f"动态隧道代理中间件: DynamicProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}"
        )


class AbuDynamicProxyDownloaderMiddleware(object):
    """
    阿布云动态代理 - 隧道验证方式（其实和快代理的写法一致）
    """

    def __init__(self, settings):
        """
        从 scrapy 配置中取出动态隧道代理的信息
        Args:
            settings: scrapy 配置信息
        """
        dynamic_proxy_config = settings.get("DYNAMIC_PROXY_CONFIG", None)
        # 查看动态隧道代理配置是否符合要求
        is_match = ReuseOperation.if_dict_meet_min_limit(
            dict_config=dynamic_proxy_config,
            key_list=["PROXY_URL", "USERNAME", "PASSWORD"],
        )
        assert is_match, f"没有配置动态隧道代理，配置示例为：{Param.dynamic_proxy_config_example}"

        self.proxy_url = dynamic_proxy_config["PROXY_URL"]
        self.username = dynamic_proxy_config["USERNAME"]
        self.password = dynamic_proxy_config["PASSWORD"]

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.slog.info(
            f"阿布云动态隧道代理中间件: AbuDynamicProxyDownloaderMiddleware 已开启，生效脚本为: {spider.name}"
        )

    def process_request(self, request, spider):
        if request.url.startswith("https://"):
            request.meta["proxy"] = f"https://{self.proxy_url}"
        elif request.url.startswith("http://"):
            request.meta["proxy"] = f"http://{self.proxy_url}"
        else:
            spider.slog.info(f"request url error: {request.url}")

        proxy_user_pass = f"{self.username}:{self.password}"
        encoded_user_pass = "Basic " + base64.urlsafe_b64encode(
            bytes(proxy_user_pass, "ascii")
        ).decode("utf8")
        request.headers["Proxy-Authorization"] = encoded_user_pass
