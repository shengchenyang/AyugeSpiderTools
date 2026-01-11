import asyncio
from typing import Any

from ayugespidertools.common.mongodbpipe import SyncStorageHandler, store_process
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.scraper.pipelines.mongo.fantasy import AyuFtyMongoPipeline

__all__ = [
    "AyuTwistedMongoPipeline",
]


class AyuTwistedMongoPipeline(AyuFtyMongoPipeline):
    async def process_item(self, item: Any) -> Any:
        await asyncio.to_thread(self.db_insert, item)
        return item

    def db_insert(self, item: Any) -> None:
        item_dict = ReuseOperation.item_to_dict(item)
        store_process(item_dict=item_dict, db=self.db, handler=SyncStorageHandler)
