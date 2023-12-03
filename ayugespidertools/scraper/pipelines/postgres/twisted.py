from twisted.enterprise import adbapi

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.postgreserrhandle import (
    TwistedAsynchronous,
    deal_postgres_err,
)
from ayugespidertools.items import DataItem
from ayugespidertools.scraper.pipelines.postgres import AyuPostgresPipeline

__all__ = ["AyuTwistedPostgresPipeline"]


class AyuTwistedPostgresPipeline(AyuPostgresPipeline):
    """使用 twisted 的 adbapi 实现 PostgreSQL 存储场景下的异步操作"""

    def __init__(self):
        super(AyuTwistedPostgresPipeline, self).__init__()
        self.dbpool = None

    def open_spider(self, spider):
        assert hasattr(spider, "postgres_conf"), "未配置 PostgreSQL 连接信息"
        self.slog = spider.slog
        self.postgres_conf = spider.postgres_conf
        self.conn = self._connect(self.postgres_conf).close()

        _postgres_conf = {
            "user": spider.postgres_conf.user,
            "password": spider.postgres_conf.password,
            "host": spider.postgres_conf.host,
            "port": spider.postgres_conf.port,
            "dbname": spider.postgres_conf.database,
        }
        self.dbpool = adbapi.ConnectionPool(
            "psycopg", cp_reconnect=True, **_postgres_conf
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

        if isinstance(table, DataItem):
            table_name = table.key_value
            table_notes = table.notes
        else:
            table_name = table
            table_notes = ""
        note_dic = alter_item.notes_dic
        sql = self._get_sql_by_item(table=table_name, item=new_item)

        try:
            cursor.execute(sql, tuple(new_item.values()))

        except Exception as e:
            self.slog.warning(
                f"Pipe Warn: {e} & Table: {table_name} & Item: {new_item}"
            )
            cursor.execute("ROLLBACK")
            deal_postgres_err(
                TwistedAsynchronous(),
                err_msg=str(e),
                cursor=cursor,
                table=table_name,
                table_notes=table_notes,
                note_dic=note_dic,
            )
            return self.db_insert(cursor, item)
        return item

    def handle_error(self, failure, item):
        self.slog.error(f"插入数据失败:{failure}, item: {item}")
