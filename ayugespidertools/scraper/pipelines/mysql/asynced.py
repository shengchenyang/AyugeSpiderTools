from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiomysql
from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.sqlformat import AboutSql
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import MysqlAsyncPortal

__all__ = [
    "AyuAsyncMysqlPipeline",
]

if TYPE_CHECKING:
    from twisted.internet.defer import Deferred

    from ayugespidertools.common.typevars import MysqlConf
    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMysqlPipeline(MysqlPipeEnhanceMixin):
    mysql_conf: MysqlConf
    pool: aiomysql.Pool
    running_tasks: set

    def open_spider(self, spider: AyuSpider) -> Deferred:
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.running_tasks = set()
        self.mysql_conf = spider.mysql_conf
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: AyuSpider) -> None:
        self.pool = await MysqlAsyncPortal(
            db_conf=self.mysql_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                alter_item = ReuseOperation.reshape_item(item_dict)
                _table_name = alter_item.table.name
                new_item = alter_item.new_item
                if update_rule := alter_item.update_rule:
                    select_sql, select_value = AboutSql.select_generate(
                        db_table=_table_name,
                        key=["1"],
                        rule=update_rule,
                        limit=1,
                        vertical=False,
                    )
                    if _ := await cursor.execute(select_sql, select_value):
                        if update_keys := alter_item.update_keys:
                            update_set_data = ReuseOperation.get_items_by_keys(
                                data=new_item, keys=update_keys
                            )
                            update_sql, update_value = AboutSql.update_generate(
                                db_table=_table_name,
                                data=update_set_data,
                                rule=update_rule,
                            )
                            await cursor.execute(update_sql, update_value)
                        return

                sql, args = self._get_sql_by_item(
                    table=alter_item.table.name,
                    item=new_item,
                    odku_enable=self.mysql_conf.odku_enable,
                    insert_prefix=self.mysql_conf.insert_prefix,
                )
                await cursor.execute(sql, args)

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        task = asyncio.create_task(self.insert_item(item_dict))
        self.running_tasks.add(task)
        await task
        task.add_done_callback(lambda t: self.running_tasks.discard(t))
        return item

    async def _close_spider(self) -> None:
        await self.pool.wait_closed()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        self.pool.close()
        return deferred_from_coro(self._close_spider())
