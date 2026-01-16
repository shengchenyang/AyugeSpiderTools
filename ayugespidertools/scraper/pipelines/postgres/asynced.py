from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.sqlformat import GenPostgresqlAsyncpg
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.exceptions import NotConfigured
from ayugespidertools.utils.database import PostgreSQLAsyncPortal

try:
    from asyncpg.pool import Pool as PGPool  # noqa: TC002
except ImportError:
    raise NotConfigured(
        "missing psycopg_pool library, please install it. "
        "install command: pip install ayugespidertools[database]"
    )

__all__ = [
    "AyuAsyncPostgresPipeline",
]

if TYPE_CHECKING:
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    pool: PGPool
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    async def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        self.pool = await PostgreSQLAsyncPortal(
            db_conf=spider.postgres_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            alter_item = ReuseOperation.reshape_item(item_dict)
            sql, args = GenPostgresqlAsyncpg.upsert_generate(
                db_table=alter_item.table.name,
                conflict_cols=alter_item.conflict_cols,
                data=alter_item.new_item,
                update_cols=alter_item.update_keys,
            )
            await conn.execute(sql, *args)

    async def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await self.insert_item(item_dict)
        return item

    async def close_spider(self) -> None:
        await self.pool.close()
