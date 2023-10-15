import asyncio

import aiomysql
from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = [
    "AsyncMysqlPipeline",
    "AsyncNormalMysqlPipeline",
]


class AsyncNormalMysqlPipeline(AyuMysqlPipeline):
    """通过 aiomysql 实现异步写入 Mysql 数据库的普通版本"""

    def open_spider(self, spider):
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=spider.mysql_conf)
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider):
        self.loop = asyncio.get_event_loop()
        self.lock = asyncio.Lock()
        self.db = await aiomysql.connect(
            loop=self.loop,
            host=self.mysql_conf.host,
            port=self.mysql_conf.port,
            user=self.mysql_conf.user,
            password=self.mysql_conf.password,
            db=self.mysql_conf.database,
            charset=self.mysql_conf.charset,
            cursorclass=aiomysql.DictCursor,
        )

    async def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        async with self.db.cursor() as cursor:
            async with self.lock:
                alter_item = super(AsyncNormalMysqlPipeline, self).get_new_item(
                    item_dict
                )
                new_item = alter_item.new_item
                sql = self._get_sql_by_item(table=item_dict["_table"], item=new_item)
                await cursor.execute(sql, tuple(new_item.values()) * 2)
                await self.db.commit()
        return item

    async def _close_spider(self):
        pass

    def close_spider(self, spider):
        self.db.close()
        return deferred_from_coro(self._close_spider())


class AsyncMysqlPipeline(AyuMysqlPipeline):
    """通过 aiomysql 实现异步写入 Mysql 数据库的连接池版本"""

    def open_spider(self, spider):
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=spider.mysql_conf)
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider):
        self.pool = await aiomysql.create_pool(
            host=self.mysql_conf.host,
            port=self.mysql_conf.port,
            user=self.mysql_conf.user,
            password=self.mysql_conf.password,
            db=self.mysql_conf.database,
            charset=self.mysql_conf.charset,
            cursorclass=aiomysql.DictCursor,
            autocommit=True,
            maxsize=10,
            minsize=1,
        )

    async def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                alter_item = super(AsyncMysqlPipeline, self).get_new_item(item_dict)
                new_item = alter_item.new_item
                sql = self._get_sql_by_item(
                    table=item_dict["_table"],
                    item=new_item,
                )
                await asyncio.shield(cursor.execute(sql, tuple(new_item.values()) * 2))
        return item

    async def _close_spider(self):
        self.pool.close()
        await self.pool.wait_closed()

    def close_spider(self, spider):
        return deferred_from_coro(self._close_spider())
