import random

from scrapy import signals

from ayugespidertools.common.params import Param

__all__ = [
    "RandomRequestUaMiddleware",
]


class RandomRequestUaMiddleware:
    """随机请求头中间件"""

    def __init__(self):
        self.explorer_types = None
        self.explorer_weights = None

    def get_random_ua_by_weight(self) -> str:
        # 先按权重取出所需浏览器类型
        explorer_types = random.choices(
            self.explorer_types, weights=self.explorer_weights
        )
        return random.choice(Param.fake_useragent_dict[explorer_types[0]])

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        # 带权重的 ua 列表，这里是根据 fake_useragent 库中的打印信息来规划权重的。
        ua_arr = [
            {"explorer": "opera", "weight": 16},
            {"explorer": "safari", "weight": 32},
            {"explorer": "internetexplorer", "weight": 41},
            {"explorer": "firefox", "weight": 124},
            {"explorer": "chrome", "weight": 772},
        ]
        self.explorer_types = [x["explorer"] for x in ua_arr]
        self.explorer_weights = [x["weight"] for x in ua_arr]
        spider.slog.info(f"随机请求头中间件 RandomRequestUaMiddleware 已开启，生效脚本为: {spider.name}")

    def process_request(self, request, spider):
        # 根据权重来获取随机请求头 ua 信息
        request.headers.setdefault(b"User-Agent", self.get_random_ua_by_weight())
