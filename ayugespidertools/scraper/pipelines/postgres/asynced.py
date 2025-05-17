from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.exceptions import NotConfigured
from ayugespidertools.utils.database import PostgreSQLAsyncPortal

try:
    from psycopg_pool import AsyncConnectionPool
except ImportError:
    raise NotConfigured(
        "missing psycopg_pool library, please install it. "
        "install command: pip install ayugespidertools[database]"
    )

__all__ = [
    "AyuAsyncPostgresPipeline",
]

if TYPE_CHECKING:
    from twisted.internet.defer import Deferred

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    pool: AsyncConnectionPool

    def open_spider(self, spider: AyuSpider) -> Deferred:
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: AyuSpider) -> None:
        self.pool = PostgreSQLAsyncPortal(
            db_conf=spider.postgres_conf, tag=PortalTag.LIBRARY
        ).connect()
        await self.pool.open()

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        async with self.pool.connection() as conn:
            item_dict = ReuseOperation.item_to_dict(item)
            alter_item = ReuseOperation.reshape_item(item_dict)
            new_item = alter_item.new_item
            sql = self._get_sql_by_item(table=alter_item.table.name, item=new_item)
            await conn.execute(sql, tuple(new_item.values()))
        return item

    async def _close_spider(self) -> None:
        await self.pool.close()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        return deferred_from_coro(self._close_spider())
