from __future__ import annotations

from typing import TYPE_CHECKING, Any

from twisted.enterprise import adbapi

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.postgreserrhandle import (
    TwistedAsynchronous,
    deal_postgres_err,
)

__all__ = ["AyuTwistedPostgresPipeline"]

if TYPE_CHECKING:
    from twisted.python.failure import Failure

    from ayugespidertools.common.typevars import PostgreSQLConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuTwistedPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    postgres_conf: PostgreSQLConf
    dbpool: adbapi.ConnectionPool
    slog: slogT

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息"
        self.slog = spider.slog
        self.postgres_conf = spider.postgres_conf
        self._connect(self.postgres_conf).close()

        _postgres_conf = {
            "user": self.postgres_conf.user,
            "password": self.postgres_conf.password,
            "host": self.postgres_conf.host,
            "port": self.postgres_conf.port,
            "dbname": self.postgres_conf.database,
        }
        self.dbpool = adbapi.ConnectionPool(
            "psycopg", cp_reconnect=True, **_postgres_conf
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

        _table_name = alter_item.table.name
        _table_notes = alter_item.table.notes
        note_dic = alter_item.notes_dic
        sql = self._get_sql_by_item(table=_table_name, item=new_item)

        try:
            cursor.execute(sql, tuple(new_item.values()))

        except Exception as e:
            self.slog.warning(
                f"Pipe Warn: {e} & Table: {_table_name} & Item: {new_item}"
            )
            cursor.execute("ROLLBACK")
            deal_postgres_err(
                TwistedAsynchronous(),
                err_msg=str(e),
                cursor=cursor,
                table=_table_name,
                table_notes=_table_notes,
                note_dic=note_dic,
            )
            return self.db_insert(cursor, item)
        return item

    def handle_error(self, failure: Failure, item: Any) -> None:
        self.slog.error(f"插入数据失败:{failure}, item: {item}")
