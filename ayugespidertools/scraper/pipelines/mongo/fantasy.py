from typing import Optional, Type, TypeVar

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
        mongodb_config: dict,
        app_conf_manage: bool,
        collection_prefix: Optional[str] = "",
    ) -> None:
        """
        初始化 mongoDB 连接，正常的话会返回 mongoDB 的连接对象 `connect` 和 `db` 对象
        Args:
            mongodb_config: mongDB 的连接配置
            app_conf_manage: 应用配置管理是否开启，用于从 consul 中取值；
                只有当 app_conf_manage 开启且不存在本地配置 LOCAL_MONGODB_CONFIG 时，才会从 consul 中取值！
            collection_prefix: mongDB 存储集合的前缀，默认为空字符
        """
        assert any([mongodb_config, app_conf_manage]), "未配置 MongoDB 连接信息！"
        assert isinstance(collection_prefix, str), "mongoDB 所要存储的集合前缀名称需要是 str 格式！"

        self.collection_prefix = collection_prefix or ""
        self.mongodb_config = None
        # 优先从本地中取配置
        if mongodb_config:
            self.mongodb_config = ReuseOperation.dict_keys_to_lower(mongodb_config)
            super(AyuFtyMongoPipeline, self).__init__(**self.mongodb_config)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongodb_config=crawler.settings.get("LOCAL_MONGODB_CONFIG"),
            app_conf_manage=crawler.settings.get("APP_CONF_MANAGE"),
            collection_prefix=crawler.settings.get("MONGODB_COLLECTION_PREFIX", ""),
        )

    def open_spider(self, spider):
        if not self.mongodb_config:
            self.mongodb_config = ReuseOperation.dict_keys_to_lower(spider.mongodb_conf)
            super(AyuFtyMongoPipeline, self).__init__(**self.mongodb_config)

        # 用于输出日志
        if all([self.conn, self.db]):
            spider.slog.info(
                f"已连接至 host: {self.mongodb_config['host']}, database: {self.mongodb_config['database']} 的 MongoDB 目标数据库"
            )

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        """
        mongoDB 存储的方法，item["mongo_update_rule"] 用于存储查询条件，如果查询数据存在的话就更新，不存在的话就插入；
        如果没有 mongo_update_rule 则每次都新增
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
                # 判断数据中中的 alldata 的格式：
                #     1.推荐：是嵌套 dict，就像 AyuMysqlPipeline 一样 -- 这是为了通用写法风格；
                #     2. 是单层的 dict
                # 如果是嵌套格式的话，需要再转化为正常格式，因为此场景不需要像 Mysql 一样依赖备注来生成字段注释
                if any(isinstance(v, dict) for v in insert_data.values()):
                    insert_data = {
                        v: insert_data[v]["key_value"] for v in insert_data.keys()
                    }

            # 否则为旧格式
            else:
                insert_data = ReuseOperation.get_items_except_keys(
                    dict_config=item_dict,
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
