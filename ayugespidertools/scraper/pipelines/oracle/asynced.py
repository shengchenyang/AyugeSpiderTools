from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.sqlformat import GenOracle
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import OracleAsyncPortal

__all__ = ["AyuAsyncOraclePipeline"]

if TYPE_CHECKING:
    from oracledb.connection import Connection
    from oracledb.cursor import Cursor
    from twisted.internet.defer import Deferred

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncOraclePipeline(OraclePipeEnhanceMixin):
    conn: Connection
    cursor: Cursor
    running_tasks: set

    def open_spider(self, spider: AyuSpider) -> Deferred:
        assert hasattr(spider, "oracle_conf"), "未配置 Oracle 连接信息！"
        self.running_tasks = set()
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: AyuSpider) -> None:
        self.pool = OracleAsyncPortal(
            db_conf=spider.oracle_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            conn.autocommit = True
            alter_item = ReuseOperation.reshape_item(item_dict)
            new_item = alter_item.new_item
            update_keys = alter_item.update_keys
            update_rules = alter_item._update_rule
            sql, args = GenOracle.merge_generate(
                db_table=alter_item.table.name,
                match_cols=update_rules.keys(),
                data=new_item,
                update_cols=update_keys,
            )
            await conn.execute(sql, args)

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await self.insert_item(item_dict)
        return item

    async def _close_spider(self) -> None:
        await self.pool.close()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        return deferred_from_coro(self._close_spider())
