"""
@File    :  Items.py
@Time    :  2022/7/15 9:38
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from scrapy.item import Item, Field
from dataclasses import dataclass, field


__all__ = [
    "ScrapyClassicItem",
    "MysqlDataItem",
    "MongoDataItem",
    "OldMongoDataItem",
]


class ScrapyClassicItem(Item):
    """
    scrapy 经典 item 示例
    """
    # 用于存放所有字段信息
    alldata = Field()
    # 用于存放存储的表名
    table = Field()
    item_mode = Field()


@dataclass
class BaseItem:
    """
    用于构建 scrapy item 的基本结构，所有需要存储的表对应的结构都放在 alldata 中
    """
    alldata: dict = field(default=None)
    table: str = field(default=None)


@dataclass
class MysqlDataItem(BaseItem):
    """
    这个是 Scrapy item 的 Mysql 的存储结构
    """
    item_mode: str = field(default="Mysql")


@dataclass
class MongoDataItem(BaseItem):
    """
    这个是 Scrapy item 的 MongoDB 的存储结构
    这个 mongo_update_rule 字段是用于 Mongo 存储时作查询使用
    """
    item_mode: str = field(default="MongoDB")
    mongo_update_rule: dict = field(default=None)


@dataclass
class OldMongoDataItem:
    """
    这个是用于 Scrapy item 旧式写法风格存储结构中的默认字段
    这个 mongo_update_rule 字段是用于 Mongo 存储时作查询使用
    """
    item_mode: str = field(default="MongoDB")
    mongo_update_rule: dict = field(default=None)
