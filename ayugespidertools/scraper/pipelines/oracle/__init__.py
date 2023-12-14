from typing import TYPE_CHECKING, Optional, Union

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.items import DataItem

__all__ = ["AyuOraclePipeline"]

if TYPE_CHECKING:
    from oracledb.connection import Connection
    from oracledb.cursor import Cursor

    from ayugespidertools.common.typevars import AlterItem, OracleConf


class AyuOraclePipeline(OraclePipeEnhanceMixin):
    """Oracle 存储场景的 scrapy pipeline 扩展的功能示例"""

    def __init__(self):
        self.oracle_conf: Optional["OracleConf"] = None
        self.slog = None
        self.conn: Optional["Connection"] = None
        self.cursor: Optional["Cursor"] = None

    def open_spider(self, spider):
        assert hasattr(spider, "oracle_conf"), "未配置 Oracle 连接信息！"
        self.slog = spider.slog
        self.oracle_conf = spider.oracle_conf
        self.conn = self._connect(self.oracle_conf)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        self.insert_item(
            alter_item=ReuseOperation.reshape_item(item_dict), table=item_dict["_table"]
        )
        return item

    def insert_item(self, alter_item: "AlterItem", table: Union[DataItem, str]):
        """通用插入数据

        Args:
            alter_item: 经过转变后的 item
            table: 数据库表名
        """
        if not (new_item := alter_item.new_item):
            return

        table_name = table.key_value if isinstance(table, DataItem) else table
        sql = self._get_sql_by_item(table=table_name, item=new_item)

        # no err handing
        self.cursor.execute(sql, tuple(new_item.values()))
        self.conn.commit()

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()
