import asyncio
from typing import TYPE_CHECKING, Any

import aiomysql
from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = [
    "AyuAsyncMysqlPipeline",
]

if TYPE_CHECKING:
    from twisted.internet.defer import Deferred

    from ayugespidertools.common.typevars import MysqlConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMysqlPipeline(MysqlPipeEnhanceMixin):
    mysql_conf: "MysqlConf"
    slog: "slogT"
    pool: aiomysql.Pool
    running_tasks: set

    def open_spider(self, spider: "AyuSpider") -> "Deferred":
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.running_tasks = set()
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: "AyuSpider") -> None:
        self.pool = await aiomysql.create_pool(
            host=self.mysql_conf.host,
            port=self.mysql_conf.port,
            user=self.mysql_conf.user,
            password=self.mysql_conf.password,
            db=self.mysql_conf.database,
            charset=self.mysql_conf.charset,
            cursorclass=aiomysql.DictCursor,
            autocommit=True,
        )

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                alter_item = ReuseOperation.reshape_item(item_dict)
                new_item = alter_item.new_item
                sql, args = self._get_sql_by_item(
                    table=alter_item.table.name,
                    item=new_item,
                    odku_enable=self.mysql_conf.odku_enable,
                )
                await cursor.execute(sql, args)

    async def process_item(self, item: Any, spider: "AyuSpider") -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        task = asyncio.create_task(self.insert_item(item_dict))
        self.running_tasks.add(task)
        await task
        task.add_done_callback(lambda t: self.running_tasks.discard(t))
        return item

    async def _close_spider(self) -> None:
        await self.pool.wait_closed()

    def close_spider(self, spider: "AyuSpider") -> "Deferred":
        self.pool.close()
        return deferred_from_coro(self._close_spider())
