import sys

from ayugespidertools.common.mongodbpipe import Synchronize, mongodb_pipe
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.mongoclient import MongoDbBase

__all__ = [
    "AyuFtyMongoPipeline",
]


# noinspection PyMissingConstructor
class AyuFtyMongoPipeline(MongoDbBase):
    """MongoDB 存储场景的 scrapy pipeline 扩展"""

    def __init__(self):
        self.conn = None
        self.db = None
        self.sys_ver_low = sys.version_info < (3, 11)

    def open_spider(self, spider):
        assert hasattr(spider, "mongodb_conf"), "未配置 MongoDB 连接信息！"
        super(AyuFtyMongoPipeline, self).__init__(
            user=spider.mongodb_conf.user,
            password=spider.mongodb_conf.password,
            host=spider.mongodb_conf.host,
            port=spider.mongodb_conf.port,
            database=spider.mongodb_conf.database,
            authsource=spider.mongodb_conf.authsource,
            authMechanism=spider.mongodb_conf.authMechanism,
        )

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        """mongoDB 存储的方法，item["mongo_update_rule"] 用于存储查询条件，如果查询数据存在的话就更新，不存在
        的话就插入；如果没有 mongo_update_rule 字段则每次都新增。
        另外，此场景不需要像 Mysql 一样依赖备注来生成字段注释

        Args:
            item: scrapy item
            spider: scrapy spider

        Returns:
            item: scrapy item
        """
        item_dict = ReuseOperation.item_to_dict(item)
        mongodb_pipe(
            Synchronize(),
            item_dict=item_dict,
            db=self.db,
            sys_ver_low=self.sys_ver_low,
        )
        return item
