from __future__ import annotations

import asyncio
import urllib.parse
from typing import TYPE_CHECKING, Any

import motor.motor_asyncio

from ayugespidertools.common.mongodbpipe import AsyncioAsynchronous
from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = ["AyuAsyncMongoPipeline"]

if TYPE_CHECKING:
    from motor.core import AgnosticClient, AgnosticDatabase

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMongoPipeline:
    client: AgnosticClient
    db: AgnosticDatabase

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "mongodb_conf"), "未配置 MongoDB 连接信息！"
        if spider.mongodb_conf.uri is not None:
            _mongo_uri = spider.mongodb_conf.uri
        else:
            _encoded_pwd = urllib.parse.quote_plus(spider.mongodb_conf.password)
            _mongo_uri = (  # type: ignore
                f"mongodb://{spider.mongodb_conf.user}:{_encoded_pwd}"
                f"@{spider.mongodb_conf.host}:{spider.mongodb_conf.port}/"
                f"{spider.mongodb_conf.database}?authSource={spider.mongodb_conf.authsource}"
                f"&authMechanism={spider.mongodb_conf.authMechanism}",
            )

        self.client = motor.motor_asyncio.AsyncIOMotorClient(_mongo_uri)
        self.db = self.client.get_database()

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await asyncio.shield(
            AsyncioAsynchronous().process_item_template(
                item_dict=item_dict,
                db=self.db,
            )
        )
        return item

    def close_spider(self, spider: AyuSpider) -> None:
        self.client.close()
