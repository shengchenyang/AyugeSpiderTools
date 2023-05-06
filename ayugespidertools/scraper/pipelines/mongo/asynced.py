import asyncio
import urllib.parse

import motor.motor_asyncio

from ayugespidertools.common.mongodbpipe import AsyncioAsynchronous
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.utils import ToolsForAyu


class AsyncMongoPipeline(object):
    """
    通过 motor 实现异步写入 MongoDB 的存储管道
    """

    def __init__(
        self,
        collection_prefix: str = "",
    ) -> None:
        assert isinstance(collection_prefix, str), "mongoDB 所要存储的集合前缀名称需要是 str 格式！"

        self.collection_prefix = collection_prefix or ""
        self.mongo_uri = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            collection_prefix=crawler.settings.get("MONGODB_COLLECTION_PREFIX", ""),
        )

    def open_spider(self, spider):
        assert hasattr(
            spider, "mongodb_conf"
        ), "未配置 MongoDB 连接信息，请查看 .conf 或 consul 上对应配置信息！"

        _encoded_pwd = urllib.parse.quote_plus(spider.mongodb_conf.password)
        self.mongo_uri = (
            f"mongodb://{spider.mongodb_conf.user}:{_encoded_pwd}"
            f"@{spider.mongodb_conf.host}:{spider.mongodb_conf.port}/"
            f"?authSource={spider.mongodb_conf.authsource}&authMechanism=SCRAM-SHA-1",
        )
        return ReuseOperation.as_deferred(self._open_spider(spider))

    async def _open_spider(self, spider):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_uri)
        self.db = self.client[spider.mongodb_conf.database]

    async def close_spider(self, spider):
        self.client.close()

    async def process_item(self, item, spider):
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        if item_dict["item_mode"] == "MongoDB":
            await asyncio.shield(
                AsyncioAsynchronous().process_item_template(
                    item_dict=item_dict,
                    db=self.db,
                    collection_prefix=self.collection_prefix,
                )
            )
        return item
