from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ayugespidertools.common.mongodbpipe import SyncStorageHandler, store_process
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import MongoDBPortal

__all__ = ["AyuFtyMongoPipeline"]

if TYPE_CHECKING:
    import pymongo
    from pymongo import database
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class AyuFtyMongoPipeline:
    client: pymongo.MongoClient
    db: database.Database
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "mongodb_conf"), "未配置 MongoDB 连接信息！"
        mongo_portal = MongoDBPortal(db_conf=spider.mongodb_conf, tag=PortalTag.LIBRARY)
        self.client = mongo_portal.get_client()
        self.db = mongo_portal.connect()

    def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        store_process(item_dict=item_dict, db=self.db, handler=SyncStorageHandler)
        return item

    def close_spider(self) -> None:
        self.client.close()
