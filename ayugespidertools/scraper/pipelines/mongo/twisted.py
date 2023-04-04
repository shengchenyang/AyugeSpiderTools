from twisted.internet import defer, reactor

from ayugespidertools.common.MongoDBPipe import TwistedAsynchronous, mongodb_pipe
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mongo.fantasy import AyuFtyMongoPipeline

__all__ = [
    "AyuTwistedMongoPipeline",
]


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
            mongodb_pipe(
                TwistedAsynchronous(),
                item_dict=item_dict,
                db=self.db,
                collection_prefix=self.collection_prefix,
            )
            reactor.callFromThread(out.callback, item_dict)
