from pymysql import cursors
from twisted.enterprise import adbapi

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.mysqlerrhandle import TwistedAsynchronous, deal_mysql_err
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.items import DataItem
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = [
    "AyuTwistedMysqlPipeline",
]


class AyuTwistedMysqlPipeline(AyuMysqlPipeline):
    """使用 twisted 的 adbapi 实现 Mysql 存储场景下的异步操作
    注意：推荐先用 AyuFtyMysqlPipeline 使用稳定后，再迁移至此管道
    """

    def __init__(self):
        super(AyuTwistedMysqlPipeline, self).__init__()
        self.dbpool = None

    def open_spider(self, spider):
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=self.mysql_conf)

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。
        self._connect(self.mysql_conf).close()

        _mysql_conf = {
            "user": spider.mysql_conf.user,
            "password": spider.mysql_conf.password,
            "host": spider.mysql_conf.host,
            "port": spider.mysql_conf.port,
            "db": spider.mysql_conf.database,
            "charset": spider.mysql_conf.charset,
            "cursorclass": cursors.DictCursor,
        }
        self.dbpool = adbapi.ConnectionPool("pymysql", cp_reconnect=True, **_mysql_conf)
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
        alter_item = super(AyuTwistedMysqlPipeline, self).get_new_item(item)
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
            cursor.execute(sql, tuple(new_item.values()) * 2)

        except Exception as e:
            self.slog.warning(f":{e}")
            self.slog.warning(f"Item:{new_item} Table: {table_name}")
            deal_mysql_err(
                TwistedAsynchronous(),
                err_msg=str(e),
                cursor=cursor,
                charset=self.mysql_conf.charset,
                collate=self.collate,
                database=self.mysql_conf.database,
                table=table_name,
                table_notes=table_notes,
                note_dic=note_dic,
            )
            return self.db_insert(cursor, item)
        return item

    def handle_error(self, failure, item):
        self.slog.error(f"插入数据失败:{failure}, item: {item}")
