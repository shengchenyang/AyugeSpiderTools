from twisted.internet import defer, reactor

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mongo.fantasy import AyuFtyMongoPipeline

__all__ = ["AyuTwistedMongoPipeline"]


class AyuTwistedMongoPipeline(AyuFtyMongoPipeline):
    """
    使用 twisted 的 adbapi 实现 mongoDB 存储场景下的异步操作
    """

    def __init__(self, *args, **kwargs):
        super(AyuTwistedMongoPipeline, self).__init__(*args, **kwargs)

    def spider_closed(self, spider):
        if self.conn:
            self.conn.close()

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        out = defer.Deferred()
        reactor.callInThread(self.db_insert, item, out)
        yield out
        defer.returnValue(item)

    def db_insert(self, item, out):
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["item_mode"] == "MongoDB":
            insert_data = item_dict.get("alldata")
            # 如果有 alldata 字段，则其为推荐格式
            if all([insert_data, isinstance(insert_data, dict)]):
                judge_item = next(iter(insert_data.values()))
                if ReuseOperation.is_namedtuple_instance(judge_item):
                    insert_data = {
                        v: insert_data[v].key_value for v in insert_data.keys()
                    }
                elif isinstance(judge_item, dict):
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
            self.db[collection_name].update(
                item_dict["mongo_update_rule"], {"$set": insert_data}, True
            )
            reactor.callFromThread(out.callback, item_dict)
