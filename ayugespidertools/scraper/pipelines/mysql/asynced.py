from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import MysqlAsyncPortal

__all__ = [
    "AyuAsyncMysqlPipeline",
]

if TYPE_CHECKING:
    import aiomysql
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.common.typevars import MysqlConf
    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMysqlPipeline(MysqlPipeEnhanceMixin):
    mysql_conf: MysqlConf
    pool: aiomysql.Pool
    running_tasks: set
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    async def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.running_tasks = set()
        self.mysql_conf = spider.mysql_conf
        self.pool = await MysqlAsyncPortal(
            db_conf=self.mysql_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                alter_item = ReuseOperation.reshape_item(item_dict)
                insert_data = alter_item.new_item
                duplicate = None
                if update_keys := alter_item.update_keys:
                    duplicate = ReuseOperation.get_items_by_keys(
                        data=insert_data, keys=update_keys
                    )
                sql, args = self._get_sql_by_item(
                    table=alter_item.table.name,
                    item=insert_data,
                    odku_enable=self.mysql_conf.odku_enable,
                    insert_prefix=self.mysql_conf.insert_prefix,
                    duplicate=duplicate,
                )
                await cursor.execute(sql, args)

    async def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        task = asyncio.create_task(self.insert_item(item_dict))
        self.running_tasks.add(task)
        await task
        task.add_done_callback(lambda t: self.running_tasks.discard(t))
        return item

    async def close_spider(self) -> None:
        self.pool.close()
        await self.pool.wait_closed()
