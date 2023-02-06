# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import random

from scrapy import signals

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Params import Param

__all__ = [
    "RandomRequestUaMiddleware",
]


class RandomRequestUaMiddleware(object):
    """
    随机请求头中间件
    """

    def get_random_ua_by_weight(self) -> str:
        """根据权重来获取随机请求头 ua 信息"""
        # 带权重的 ua 列表，将比较常用的 ua 标识的权重设置高一点。这里是根据 fake_useragent 库中的打印信息来规划权重的。
        ua_arr = [
            {"explorer_type": "opera", "weight": 16},
            {"explorer_type": "safari", "weight": 32},
            {"explorer_type": "internetexplorer", "weight": 41},
            {"explorer_type": "firefox", "weight": 124},
            {"explorer_type": "chrome", "weight": 772},
        ]
        curr_ua_type = ReuseOperation.random_weight(weight_data=ua_arr)
        curr_ua_list = Param.fake_useragent_dict[curr_ua_type["explorer_type"]]
        return random.choice(curr_ua_list)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.slog.info(f"随机请求头中间件 RandomRequestUaMiddleware 已开启，生效脚本为: {spider.name}")

    def process_request(self, request, spider):
        if curr_ua := self.get_random_ua_by_weight():
            request.headers.setdefault(b"User-Agent", curr_ua)
            spider.slog.debug(f"RandomRequestUaMiddleware 当前使用的 ua 为: {curr_ua}")
