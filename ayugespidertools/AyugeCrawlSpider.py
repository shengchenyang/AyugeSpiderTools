#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  AyugeSpider.py
@Time    :  2022/1/3 10:33
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from scrapy.spiders import Spider, CrawlSpider
from ayugespidertools.AyugeSpider import AyuSpider


__all__ = [
    "AyuCrawlSpider",
]


class AyuCrawlSpider(AyuSpider, CrawlSpider):
    """
    初始 AyuSpider 配置，也初始化 CrawlSpider 的 spider 加强版本配置
    """

    def __init__(self, *args, **kwargs):
        AyuSpider.__init__(self, *args, **kwargs)
        CrawlSpider.__init__(self, *args, **kwargs)
