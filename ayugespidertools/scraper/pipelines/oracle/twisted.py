from __future__ import annotations

from typing import TYPE_CHECKING, Any

from twisted.enterprise import adbapi

from ayugespidertools.common.expend import OraclePipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = [
    "AyuTwistedOraclePipeline",
]

if TYPE_CHECKING:
    from oracledb.connection import Connection
    from twisted.python.failure import Failure

    from ayugespidertools.common.typevars import OracleConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuTwistedOraclePipeline(OraclePipeEnhanceMixin):
    oracle_conf: OracleConf
    slog: slogT
    conn: Connection
    dbpool: adbapi.ConnectionPool

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "oracle_conf"), "未配置 Oracle 连接信息！"
        self.slog = spider.slog
        self.oracle_conf = spider.oracle_conf

        _oracle_conf = {
            "user": self.oracle_conf.user,
            "password": self.oracle_conf.password,
            "host": self.oracle_conf.host,
            "port": self.oracle_conf.port,
            "service_name": self.oracle_conf.service_name,
            "encoding": self.oracle_conf.encoding,
            "config_dir": self.oracle_conf.thick_lib_dir or None,
        }
        self.dbpool = adbapi.ConnectionPool(
            "oracledb", cp_reconnect=True, **_oracle_conf
        )
        query = self.dbpool.runInteraction(self.db_create)
        query.addErrback(self.db_create_err)

    def db_create(self, cursor: Any) -> None: ...

    def db_create_err(self, failure: Failure) -> None:
        self.slog.error(f"创建数据表失败: {failure}")

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        query = self.dbpool.runInteraction(self.db_insert, item_dict)
        query.addErrback(self.handle_error, item)
        return item

    def db_insert(self, cursor: Any, item: Any) -> Any:
        alter_item = ReuseOperation.reshape_item(item)
        if not (new_item := alter_item.new_item):
            return

        sql = self._get_sql_by_item(table=alter_item.table.name, item=new_item)
        cursor.execute(sql, tuple(new_item.values()))
        return item

    def handle_error(self, failure: Failure, item: Any) -> None:
        self.slog.error(f"插入数据失败:{failure}, item: {item}")
