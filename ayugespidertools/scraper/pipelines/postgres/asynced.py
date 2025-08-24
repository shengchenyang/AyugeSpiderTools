from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.sqlformat import GenPostgresqlAsyncpg
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.exceptions import NotConfigured
from ayugespidertools.utils.database import PostgreSQLAsyncPortal

try:
    from asyncpg.pool import Pool as PGPool
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
    pool: PGPool

    def open_spider(self, spider: AyuSpider) -> Deferred:
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: AyuSpider) -> None:
        self.pool = await PostgreSQLAsyncPortal(
            db_conf=spider.postgres_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            alter_item = ReuseOperation.reshape_item(item_dict)
            _table_name = alter_item.table.name
            new_item = alter_item.new_item
            update_keys = alter_item.update_keys
            sql, args = GenPostgresqlAsyncpg.upsert_generate(
                db_table=_table_name,
                conflict_cols=alter_item.conflict_cols,
                data=new_item,
                update_cols=update_keys,
            )
            await conn.execute(sql, *args)

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await self.insert_item(item_dict)

    async def _close_spider(self) -> None:
        await self.pool.close()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        return deferred_from_coro(self._close_spider())
