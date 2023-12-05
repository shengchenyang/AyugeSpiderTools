import datetime
import warnings
from typing import TYPE_CHECKING, Optional, Union

import pymysql

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.mysqlerrhandle import Synchronize, deal_mysql_err
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.items import DataItem

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

    from ayugespidertools.common.typevars import AlterItem, MysqlConf


class AyuMysqlPipeline(MysqlPipeEnhanceMixin):
    """Mysql 存储场景的 scrapy pipeline 扩展的主要功能示例"""

    def __init__(self) -> None:
        # 排序规则，用于创建数据库时使用
        self.collate: str = ""
        self.mysql_conf: Optional["MysqlConf"] = None
        self.conn: Optional["Connection[Cursor]"] = None
        self.slog = None
        self.cursor: Optional["Cursor"] = None
        self.crawl_time = datetime.date.today()

    def open_spider(self, spider):
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=self.mysql_conf)
        self.conn = self._connect(self.mysql_conf)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        self.insert_item(
            alter_item=ReuseOperation.reshape_item(item_dict),
            table=item_dict["_table"],
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

        if isinstance(table, DataItem):
            table_name = table.key_value
            table_notes = table.notes
        else:
            table_name = table
            table_notes = ""
        note_dic = alter_item.notes_dic
        sql = self._get_sql_by_item(table=table_name, item=new_item)

        try:
            self.cursor.execute(sql, tuple(new_item.values()) * 2)
            self.conn.commit()

        except Exception as e:
            self.slog.warning(
                f"Pipe Warn: {e} & Table: {table_name} & Item: {new_item}"
            )
            self.conn.rollback()
            deal_mysql_err(
                Synchronize(),
                err_msg=str(e),
                conn=self.conn,
                cursor=self.cursor,
                charset=self.mysql_conf.charset,
                collate=self.collate,
                database=self.mysql_conf.database,
                table=table_name,
                table_notes=table_notes,
                note_dic=note_dic,
            )
            return self.insert_item(alter_item, table)

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()
