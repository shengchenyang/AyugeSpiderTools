from __future__ import annotations

import json
import random
from pathlib import Path
from typing import TYPE_CHECKING

from scrapy import signals

from ayugespidertools.config import NormalConfig

__all__ = [
    "RandomRequestUaMiddleware",
]

if TYPE_CHECKING:
    from scrapy import Request
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class RandomRequestUaMiddleware:
    """随机请求头中间件"""

    def __init__(self):
        self.explorer_types = None
        self.explorer_weights = None
        _ua_file = Path(NormalConfig.DATA_DIR, "browsers.json")
        self.fake_ua_dict = json.loads(_ua_file.read_text(encoding="utf-8"))

    def get_random_ua_by_weight(self) -> str:
        explorer_types = random.choices(
            self.explorer_types, weights=self.explorer_weights
        )
        return random.choice(self.fake_ua_dict[explorer_types[0]])

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider: AyuSpider) -> None:
        # 带权重的 ua 列表
        ua_arr = [
            {"explorer": "safari", "weight": 50},
            {"explorer": "edge", "weight": 9},
            {"explorer": "firefox", "weight": 50},
            {"explorer": "chrome", "weight": 3},
        ]
        self.explorer_types = [x["explorer"] for x in ua_arr]
        self.explorer_weights = [x["weight"] for x in ua_arr]
        spider.slog.info(
            f"随机请求头中间件 RandomRequestUaMiddleware 已开启，生效脚本为: {spider.name}"
        )

    def process_request(self, request: Request, spider: AyuSpider) -> None:
        request.headers.setdefault(b"User-Agent", self.get_random_ua_by_weight())
