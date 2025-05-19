from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import pymysql

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.mysqlerrhandle import Synchronize, deal_mysql_err

# 将 pymysql 中 Data truncated for column 警告类型置为 Error，其他警告忽略
warnings.filterwarnings(
    "error", category=pymysql.Warning, message=".*Data truncated for column.*"
)

__all__ = [
    "AyuMysqlPipeline",
]

if TYPE_CHECKING:
    from pymysql.connections import Connection
    from pymysql.cursors import Cursor

    from ayugespidertools.common.typevars import AlterItem, MysqlConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuMysqlPipeline(MysqlPipeEnhanceMixin):
    mysql_conf: MysqlConf
    conn: Connection
    slog: slogT
    cursor: Cursor

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.conn = self._connect(self.mysql_conf)
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
        sql, args = self._get_sql_by_item(
            table=_table_name,
            item=new_item,
            odku_enable=self.mysql_conf.odku_enable,
            insert_prefix=self.mysql_conf.insert_prefix,
        )

        try:
            self.cursor.execute(sql, args)
            self.conn.commit()
        except Exception as e:
            self.slog.warning(
                f"Pipe Warn: {e} & Table: {_table_name} & Item: {new_item}"
            )
            self.conn.rollback()
            deal_mysql_err(
                Synchronize(),
                err_msg=str(e),
                conn=self.conn,
                cursor=self.cursor,
                mysql_conf=self.mysql_conf,
                table=_table_name,
                table_notes=_table_notes,
                note_dic=note_dic,
            )
            return self.insert_item(alter_item)

    def close_spider(self, spider: AyuSpider) -> None:
        self.conn.close()
