from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ayugespidertools.common.expend import PostgreSQLPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.postgreserrhandle import Synchronize, deal_postgres_err
from ayugespidertools.common.sqlformat import GenPostgresql

__all__ = ["AyuPostgresPipeline"]

if TYPE_CHECKING:
    from psycopg.connection import Connection
    from psycopg.cursor import Cursor

    from ayugespidertools.common.typevars import AlterItem, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuPostgresPipeline(PostgreSQLPipeEnhanceMixin):
    conn: Connection
    slog: slogT
    cursor: Cursor

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息！"
        self.slog = spider.slog
        self.conn = self._connect(spider.postgres_conf)
        self.cursor = self.conn.cursor()

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alter_item = ReuseOperation.reshape_item(item_dict)
        self.insert_item(alter_item)
        return item

    def insert_item(self, alter_item: AlterItem) -> None:
        if not (new_item := alter_item.new_item):
            return

        _table_name = alter_item.table.name
        _table_notes = alter_item.table.notes
        note_dic = alter_item.notes_dic
        if update_rule := alter_item.update_rule:
            select_sql, select_value = GenPostgresql.select_generate(
                db_table=_table_name,
                key=["1"],
                rule=update_rule,
                limit=1,
                vertical=False,
            )
            self.cursor.execute(select_sql, select_value)
            if self.cursor.rowcount:
                if update_keys := alter_item.update_keys:
                    update_set_data = ReuseOperation.get_items_by_keys(
                        data=new_item, keys=update_keys
                    )
                    update_sql, update_value = GenPostgresql.update_generate(
                        db_table=_table_name,
                        data=update_set_data,
                        rule=update_rule,
                    )
                    self.cursor.execute(update_sql, update_value)
                    self.conn.commit()
                return

        sql = self._get_sql_by_item(table=_table_name, item=new_item)
        try:
            self.cursor.execute(sql, tuple(new_item.values()))
            self.conn.commit()

        except Exception as e:
            self.slog.warning(
                f"Pipe Warn: {e} & Table: {_table_name} & Item: {new_item}"
            )
            self.conn.rollback()
            deal_postgres_err(
                Synchronize(),
                err_msg=str(e),
                conn=self.conn,
                cursor=self.cursor,
                table=_table_name,
                table_notes=_table_notes,
                note_dic=note_dic,
            )
            return self.insert_item(alter_item)

    def close_spider(self, spider: AyuSpider) -> None:
        self.cursor.close()
        self.conn.close()
