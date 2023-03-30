from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.MongoClient import MongoDbBase

__all__ = ["AyuFtyMongoPipeline"]


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
        self.mongodb_conf = None
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
        self.mongodb_conf = ReuseOperation.dict_keys_to_lower(spider.mongodb_conf)
        super(AyuFtyMongoPipeline, self).__init__(**self.mongodb_conf)

        # 用于输出日志
        if all([self.conn, self.db]):
            spider.slog.info(
                f"已连接至 host: {self.mongodb_conf['host']}, database: {self.mongodb_conf['database']} 的 MongoDB 目标数据库"
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
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["item_mode"] == "MongoDB":
            insert_data = item_dict.get("alldata")
            # 如果有 alldata 字段，则其为推荐格式
            if all([insert_data, isinstance(insert_data, dict)]):
                judge_item = next(iter(insert_data.values()))
                # 判断数据中中的 alldata 的格式：
                #     1.推荐：是嵌套 dict，就像 AyuMysqlPipeline 一样 -- 这是为了通用写法风格；
                #     2.是单层的 dict
                # 是 namedtuple 类型
                if ReuseOperation.is_namedtuple_instance(judge_item):
                    insert_data = {
                        v: insert_data[v].key_value for v in insert_data.keys()
                    }
                # 如果是嵌套 dict 格式的话，需要再转化为正常格式
                elif isinstance(judge_item, dict):
                    insert_data = {
                        v: insert_data[v]["key_value"] for v in insert_data.keys()
                    }

            # 否则为旧格式
            else:
                insert_data = ReuseOperation.get_items_except_keys(
                    dict_conf=item_dict,
                    key_list=["table", "item_mode", "mongo_update_rule"],
                )

            # 真实的集合名称为：集合前缀名 + 集合名称
            collection_name = f"""{self.collection_prefix}{item_dict["table"]}"""
            # 如果没有查重字段时，就直接插入数据（不去重）
            if not item_dict.get("mongo_update_rule"):
                self.db[collection_name].insert(insert_data)
            else:
                self.db[collection_name].update(
                    item_dict["mongo_update_rule"], {"$set": insert_data}, True
                )
        return item
