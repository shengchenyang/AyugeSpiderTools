from ayugespidertools.common.mongodbpipe import Synchronize, mongodb_pipe
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.mongoclient import MongoDbBase

__all__ = [
    "AyuFtyMongoPipeline",
]


class AyuFtyMongoPipeline(MongoDbBase):
    """
    MongoDB 存储场景的 scrapy pipeline 扩展
    """

    def __init__(
        self,
        collection_prefix: str = "",
    ) -> None:
        """
        初始化
        Args:
            mongodb_conf: mongDB 的连接配置
            collection_prefix: mongDB 存储集合的前缀，默认为空字符
        """
        assert isinstance(collection_prefix, str), "mongoDB 所要存储的集合前缀名称需要是 str 格式！"

        self.collection_prefix = collection_prefix or ""
        # conn 和 db 为父类的属性，用于存储连接信息
        self.conn = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            collection_prefix=crawler.settings.get("MONGODB_COLLECTION_PREFIX", ""),
        )

    def open_spider(self, spider):
        assert hasattr(
            spider, "mongodb_conf"
        ), "未配置 MongoDB 连接信息，请查看 .conf 或 consul 上对应配置信息！"
        super(AyuFtyMongoPipeline, self).__init__(
            user=spider.mongodb_conf.user,
            password=spider.mongodb_conf.password,
            host=spider.mongodb_conf.host,
            port=spider.mongodb_conf.port,
            database=spider.mongodb_conf.database,
            authsource=spider.mongodb_conf.authsource,
        )

        # 用于输出日志
        if all([self.conn, self.db]):
            spider.slog.info(
                f"已连接至 host: {spider.mongodb_conf.host}, "
                f"database: {spider.mongodb_conf.database} 的 MongoDB 目标数据库"
            )

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        """
        mongoDB 存储的方法，item["mongo_update_rule"] 用于存储查询条件，如果查询数据存在的话就更新，不存在的话就插入；
        如果没有 mongo_update_rule 则每次都新增
        此场景不需要像 Mysql 一样依赖备注来生成字段注释
        Args:
            item: scrapy item
            spider: scrapy spider

        Returns:
            item: scrapy item
        """
        item_dict = ReuseOperation.item_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["_item_mode"] == "MongoDB":
            mongodb_pipe(
                Synchronize(),
                item_dict=item_dict,
                db=self.db,
                collection_prefix=self.collection_prefix,
            )
        return item
