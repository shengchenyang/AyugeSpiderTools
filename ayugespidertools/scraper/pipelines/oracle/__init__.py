from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = ["AyuOraclePipeline"]

if TYPE_CHECKING:
    from oracledb.connection import Connection
    from oracledb.cursor import Cursor

    from ayugespidertools.common.typevars import AlterItem
    from ayugespidertools.spiders import AyuSpider


class AyuOraclePipeline(OraclePipeEnhanceMixin):
    conn: Connection
    cursor: Cursor

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "oracle_conf"), "未配置 Oracle 连接信息！"
        self.conn = self._connect(spider.oracle_conf)
        self.cursor = self.conn.cursor()

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alter_item = ReuseOperation.reshape_item(item_dict)
        self.insert_item(alter_item)
        return item

    def insert_item(self, alter_item: AlterItem) -> None:
        if not (new_item := alter_item.new_item):
            return

        sql = self._get_sql_by_item(table=alter_item.table.name, item=new_item)
        self.cursor.execute(sql, tuple(new_item.values()))
        self.conn.commit()

    def close_spider(self, spider: AyuSpider) -> None:
        self.conn.close()
