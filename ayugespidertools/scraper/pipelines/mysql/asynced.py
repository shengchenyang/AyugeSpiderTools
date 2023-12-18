import asyncio
from typing import TYPE_CHECKING, Optional

import aiomysql
from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = [
    "AyuAsyncMysqlPipeline",
]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import MysqlConf


class AyuAsyncMysqlPipeline(MysqlPipeEnhanceMixin):
    """结合 aiomysql 实现异步写入 Mysql 数据库"""

    def __init__(self) -> None:
        self.mysql_conf: Optional["MysqlConf"] = None
        self.slog = None
        self.pool = None
        self.running_tasks = set()

    def open_spider(self, spider):
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
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
        )

    async def my_coroutine(self, item_dict):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                alter_item = ReuseOperation.reshape_item(item_dict)
                new_item = alter_item.new_item
                sql = self._get_sql_by_item(
                    table=item_dict["_table"],
                    item=new_item,
                    odku_enable=False,
                )
                await cursor.execute(sql, tuple(new_item.values()))

    async def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        task = asyncio.create_task(self.my_coroutine(item_dict))
        self.running_tasks.add(task)
        await task
        task.add_done_callback(lambda t: self.running_tasks.remove(t))
        return item

    async def _close_spider(self):
        await self.pool.wait_closed()

    def close_spider(self, spider):
        self.pool.close()
        return deferred_from_coro(self._close_spider())
