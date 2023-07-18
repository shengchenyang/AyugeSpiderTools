from scrapy.spiders import CrawlSpider

from ayugespidertools.scraper.spiders import AyuSpider

__all__ = [
    "AyuCrawlSpider",
]


class AyuCrawlSpider(AyuSpider, CrawlSpider):
    """初始 AyuSpider 配置，也初始化 CrawlSpider 的 spider 加强版本配置"""

    def __init__(self, *args, **kwargs):
        AyuSpider.__init__(self, *args, **kwargs)
        CrawlSpider.__init__(self, *args, **kwargs)
