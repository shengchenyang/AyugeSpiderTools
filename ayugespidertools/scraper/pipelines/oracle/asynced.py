from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.sqlformat import GenOracle
from ayugespidertools.common.typevars import PortalTag
from ayugespidertools.utils.database import OracleAsyncPortal

__all__ = ["AyuAsyncOraclePipeline"]

if TYPE_CHECKING:
    import oracledb
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.spiders import AyuSpider


class AyuAsyncOraclePipeline(OraclePipeEnhanceMixin):
    running_tasks: set
    crawler: Crawler
    pool: oracledb.AsyncConnectionPool

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    async def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "oracle_conf"), "未配置 Oracle 连接信息！"
        self.running_tasks = set()
        self.pool = OracleAsyncPortal(
            db_conf=spider.oracle_conf, tag=PortalTag.LIBRARY
        ).connect()

    async def insert_item(self, item_dict: dict) -> None:
        async with self.pool.acquire() as conn:
            conn.autocommit = True
            alter_item = ReuseOperation.reshape_item(item_dict)
            sql, args = GenOracle.merge_generate(
                db_table=alter_item.table.name,
                match_cols=alter_item.update_rule,
                data=alter_item.new_item,
                update_cols=alter_item.update_keys,
            )
            await conn.execute(sql, args)

    async def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        await self.insert_item(item_dict)
        return item

    async def close_spider(self) -> None:
        await self.pool.close()
