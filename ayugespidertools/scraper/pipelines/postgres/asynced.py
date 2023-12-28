from typing import TYPE_CHECKING, Optional

from psycopg_pool import AsyncConnectionPool
from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import PostgreSQLConf

__all__ = [
    "AyuAsyncPostgresPipeline",
]


class AyuAsyncPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    """postgresql asyncio 版本"""

    def __init__(self) -> None:
        self.postgres_conf: Optional["PostgreSQLConf"] = None
        self.slog = None
        self.pool = None
        self.running_tasks: set = set()

    def open_spider(self, spider):
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        self.slog = spider.slog
        self.postgres_conf = spider.postgres_conf
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider):
        self.pool = AsyncConnectionPool(
            f"dbname={self.postgres_conf.database} "
            f"user={self.postgres_conf.user} "
            f"host={self.postgres_conf.host} "
            f"port={self.postgres_conf.port} "
            f"password={self.postgres_conf.password}",
            open=False,
        )
        await self.pool.open()

    async def process_item(self, item, spider):
        async with self.pool.connection() as conn:
            item_dict = ReuseOperation.item_to_dict(item)
            alter_item = ReuseOperation.reshape_item(item_dict)
            new_item = alter_item.new_item
            sql = self._get_sql_by_item(table=alter_item.table.name, item=new_item)
            await conn.execute(sql, tuple(new_item.values()))
        return item

    async def _close_spider(self):
        await self.pool.close()

    def close_spider(self, spider):
        return deferred_from_coro(self._close_spider())