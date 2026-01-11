from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ayugespidertools.common.mongodbpipe import AsyncStorageHandler, store_process_async
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import MongoDBAsyncPortal

__all__ = ["AyuAsyncMongoPipeline"]

if TYPE_CHECKING:
    from motor.core import AgnosticClient, AgnosticDatabase
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMongoPipeline:
    client: AgnosticClient
    db: AgnosticDatabase
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "mongodb_conf"), "未配置 MongoDB 连接信息！"
        mongo_portal = MongoDBAsyncPortal(
            db_conf=spider.mongodb_conf, tag=PortalTag.LIBRARY
        )
        self.client = mongo_portal.get_client()
        self.db = mongo_portal.connect()

    async def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await store_process_async(
            item_dict=item_dict, db=self.db, handler=AsyncStorageHandler
        )
        return item

    def close_spider(self) -> None:
        self.client.close()
