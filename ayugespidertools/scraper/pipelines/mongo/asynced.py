from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ayugespidertools.common.mongodbpipe import AsyncStorageHandler, store_process_async
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import MongoDBAsyncPortal

__all__ = ["AyuAsyncMongoPipeline"]

if TYPE_CHECKING:
    from motor.core import AgnosticClient, AgnosticDatabase

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMongoPipeline:
    client: AgnosticClient
    db: AgnosticDatabase

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "mongodb_conf"), "未配置 MongoDB 连接信息！"
        mongo_portal = MongoDBAsyncPortal(
            db_conf=spider.mongodb_conf, tag=PortalTag.LIBRARY
        )
        self.client = mongo_portal.get_client()
        self.db = mongo_portal.connect()

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await store_process_async(
            item_dict=item_dict, db=self.db, handler=AsyncStorageHandler
        )
        return item

    def close_spider(self, spider: AyuSpider) -> None:
        self.client.close()
