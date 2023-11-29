from typing import TYPE_CHECKING, Optional, TypeVar, Union

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.postgreserrhandle import Synchronize, deal_postgres_err
from ayugespidertools.items import DataItem

__all__ = ["AyuPostgresPipeline"]


if TYPE_CHECKING:
    from psycopg.connection import Connection
    from psycopg.cursor import Cursor

    from ayugespidertools.common.typevars import AlterItem, PostgreSQLConf

    PsycopgConnectT = TypeVar("PsycopgConnectT", bound=Connection)
    PsycopgCursorT = TypeVar("PsycopgCursorT", bound=Cursor)


class AyuPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    """Postgresql 存储场景的 scrapy pipeline 扩展的主要功能示例"""

    def __init__(self) -> None:
        self.postgres_conf: Optional["PostgreSQLConf"] = None
        self.conn: Optional["PsycopgConnectT"] = None
        self.slog = None
        self.cursor: Optional["PsycopgCursorT"] = None

    def open_spider(self, spider):
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        self.slog = spider.slog
        self.postgres_conf = spider.postgres_conf
        self.conn = self._connect(self.postgres_conf)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        self.insert_item(
            alter_item=ReuseOperation.reshape_item(item_dict),
            table=item_dict["_table"],
        )
        return item

    def insert_item(self, alter_item: "AlterItem", table: Union[DataItem, str]):
        if not (new_item := alter_item.new_item):
            return

        if isinstance(table, DataItem):
            table_name = table.key_value
            table_notes = table.notes
        else:
            table_name = table
            table_notes = ""
        note_dic = alter_item.notes_dic
        sql = self._get_sql_by_item(table=table_name, item=new_item)

        try:
            if self.cursor.execute(sql, tuple(new_item.values())):
                self.conn.commit()

        except Exception as e:
            self.slog.warning(f"{e}")
            self.slog.warning(f"Item: {new_item} Table: {table_name}")
            self.conn.rollback()
            deal_postgres_err(
                Synchronize(),
                err_msg=str(e),
                conn=self.conn,
                cursor=self.cursor,
                table=table_name,
                table_notes=table_notes,
                note_dic=note_dic,
            )
            return self.insert_item(alter_item, table)

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
