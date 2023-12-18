from typing import TYPE_CHECKING, Optional

from twisted.enterprise import adbapi

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.items import DataItem

__all__ = [
    "AyuTwistedOraclePipeline",
]

if TYPE_CHECKING:
    from oracledb.connection import Connection

    from ayugespidertools.common.typevars import OracleConf


class AyuTwistedOraclePipeline(OraclePipeEnhanceMixin):
    """Oracle 存储场景下的异步操作"""

    def __init__(self):
        self.oracle_conf: Optional["OracleConf"] = None
        self.slog = None
        self.conn: Optional["Connection"] = None
        self.dbpool = None

    def open_spider(self, spider):
        assert hasattr(spider, "oracle_conf"), "未配置 Oracle 连接信息！"
        self.slog = spider.slog
        self.oracle_conf = spider.oracle_conf

        _oracle_conf = {
            "user": spider.oracle_conf.user,
            "password": spider.oracle_conf.password,
            "host": spider.oracle_conf.host,
            "port": spider.oracle_conf.port,
            "service_name": spider.oracle_conf.service_name,
            "encoding": spider.oracle_conf.encoding,
            "config_dir": spider.oracle_conf.thick_lib_dir or None,
        }
        self.dbpool = adbapi.ConnectionPool(
            "oracledb", cp_reconnect=True, **_oracle_conf
        )
        query = self.dbpool.runInteraction(self.db_create)
        query.addErrback(self.db_create_err)

    def db_create(self, cursor):
        pass

    def db_create_err(self, failure):
        self.slog.error(f"创建数据表失败: {failure}")

    def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        query = self.dbpool.runInteraction(self.db_insert, item_dict)
        query.addErrback(self.handle_error, item)
        return item

    def db_insert(self, cursor, item):
        alter_item = ReuseOperation.reshape_item(item)
        table = item["_table"]

        if not (new_item := alter_item.new_item):
            return

        table_name = table.key_value if isinstance(table, DataItem) else table
        sql = self._get_sql_by_item(table=table_name, item=new_item)

        cursor.execute(sql, tuple(new_item.values()))
        return item

    def handle_error(self, failure, item):
        self.slog.error(f"插入数据失败:{failure}, item: {item}")
