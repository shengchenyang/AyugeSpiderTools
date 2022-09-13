#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from enum import Enum


class TableEnum(Enum):
    """
    数据库表枚举信息
    """

    # 文章列表信息
    aritle_list_table = {"value": "article_info_list", "notes": "项目列表信息", "demand_code": "DemoSpider_aritle_list_table_demand_code"}

    # 小说列表信息
    book_info_list_table = {"value": "book_info_list", "notes": "小说列表信息", "demand_code": "DemoSpider_book_info_list_table_demand_code"}
