from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ayugespidertools.common.mongodbpipe import Synchronize, mongodb_pipe
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import MongoDBPortal

__all__ = ["AyuFtyMongoPipeline"]

if TYPE_CHECKING:
    import pymongo
    from pymongo import database

    from ayugespidertools.spiders import AyuSpider


class AyuFtyMongoPipeline:
    client: pymongo.MongoClient
    db: database.Database

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "mongodb_conf"), "未配置 MongoDB 连接信息！"
        mongo_portal = MongoDBPortal(db_conf=spider.mongodb_conf, tag=PortalTag.LIBRARY)
        self.client = mongo_portal.get_client()
        self.db = mongo_portal.connect()

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        """mongoDB 存储的方法，item["_mongo_update_rule"] 用于存储查询条件，如果查询数据存在的话
        就更新，不存在的话就插入；如果没有 mongo_update_rule 字段则每次都新增。

        Args:
            item: scrapy item
            spider: scrapy spider

        Returns:
            item: scrapy item
        """
        item_dict = ReuseOperation.item_to_dict(item)
        mongodb_pipe(Synchronize(), item_dict=item_dict, db=self.db)
        return item

    def close_spider(self, spider: AyuSpider) -> None:
        self.client.close()
