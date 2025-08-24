from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.sqlformat import GenOracle

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

        update_keys = alter_item.update_keys
        update_rules = alter_item._update_rule
        sql, args = GenOracle.merge_generate(
            db_table=alter_item.table.name,
            match_cols=update_rules.keys(),
            data=new_item,
            update_cols=update_keys,
        )
        self.cursor.execute(sql, args)
        self.conn.commit()

    def close_spider(self, spider: AyuSpider) -> None:
        self.conn.close()
