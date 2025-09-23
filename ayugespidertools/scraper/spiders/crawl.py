from __future__ import annotations

from typing import Any

from scrapy.spiders import CrawlSpider

from ayugespidertools.scraper.spiders import AyuSpider

__all__ = [
    "AyuCrawlSpider",
]


class AyuCrawlSpider(AyuSpider, CrawlSpider):  # type: ignore[misc]
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
