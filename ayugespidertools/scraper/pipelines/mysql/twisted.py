from pymysql import cursors
from twisted.enterprise import adbapi

from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = ["AyuTwistedMysqlPipeline"]


class AyuTwistedMysqlPipeline(AyuMysqlPipeline):
    """
    使用 twisted 的 adbapi 实现 Mysql 存储场景下的异步操作
    注意：
        1. 推荐先用 AyuFtyMysqlPipeline 使用稳定后，再迁移至此管道
    """

    def __init__(self, *args, **kwargs):
        super(AyuTwistedMysqlPipeline, self).__init__(*args, **kwargs)
        self.dbpool = None

    def open_spider(self, spider):
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=self.mysql_conf)

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。
        # 记录日志时需要此连接对象，否则直接关闭
        if self.record_log_to_mysql:
            self.conn = self._connect(pymysql_dict_conf=self.mysql_conf)
            self.cursor = self.conn.cursor()
        else:
            self._connect(pymysql_dict_conf=self.mysql_conf).close()

        self.mysql_conf["cursorclass"] = cursors.DictCursor
        self.dbpool = adbapi.ConnectionPool(
            "pymysql", cp_reconnect=True, **self.mysql_conf
        )
        query = self.dbpool.runInteraction(self.db_create)
        query.addErrback(self.db_create_err)

    def db_create(self, cursor):
        pass

    def db_create_err(self, failure):
        self.slog.error(f"创建数据表失败: {failure}")

    def process_item(self, item, spider):
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["item_mode"] == "Mysql":
            query = self.dbpool.runInteraction(self.db_insert, item_dict)
            query.addErrback(self.handle_error, item)
        return item

    def db_insert(self, cursor, item):
        item_o = super(AyuTwistedMysqlPipeline, self).get_new_item(item)
        table = super(AyuTwistedMysqlPipeline, self).get_table_name(item["table"])

        # 以下逻辑直接 copy 父类的 insert_item 方法，只是剔除了 commit 方法和修改 cursor 而已
        new_item = item_o.get("new_item")
        note_dic = item_o.get("notes_dic")
        keys = f"""`{"`, `".join(new_item.keys())}`"""
        values = ", ".join(["%s"] * len(new_item))
        update = ",".join([f" `{key}` = %s" for key in new_item])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"

        try:
            cursor.execute(sql, tuple(new_item.values()) * 2)

        except Exception as e:
            self.slog.warning(f":{e}")
            self.slog.warning(f"Item:{new_item}  Table: {table}")
            err_msg = str(e)
            if "1054" in err_msg:
                self.deal_1054_error(
                    err_msg=err_msg,
                    conn=None,
                    cursor=cursor,
                    table=table,
                    note_dic=note_dic,
                )
                return self.db_insert(cursor, item)

            elif "1146" in err_msg:
                self.deal_1146_error(
                    err_msg=err_msg,
                    table_prefix=self.table_prefix,
                    cursor=cursor,
                    charset=self.mysql_conf["charset"],
                    collate=self.collate,
                    table_enum=self.table_enum,
                )
                return self.db_insert(cursor, item)

            elif "1406" in err_msg:
                self.deal_1406_error(
                    err_msg=err_msg,
                    conn=None,
                    cursor=cursor,
                    database=self.mysql_conf["database"],
                    table=table,
                    note_dic=note_dic,
                )
                return self.db_insert(cursor, item)

            elif "1265" in err_msg:
                self.deal_1265_error(
                    err_msg=err_msg,
                    conn=None,
                    cursor=cursor,
                    database=self.mysql_conf["database"],
                    table=table,
                    note_dic=note_dic,
                )
                return self.db_insert(cursor, item)

            else:
                # 碰到其他的异常才打印错误日志，已处理的异常不打印
                self.slog.error(f"ERROR:{e}")

        return item

    def handle_error(self, failure, item):
        self.slog.error(f"插入数据失败:{failure}, item: {item}")

    def close_spider(self, spider):
        # 不删除 cursorclass 其实也不影响
        if "cursorclass" in self.mysql_conf.keys():
            del self.mysql_conf["cursorclass"]

        # 这里新建数据库链接，是为了正常继承父类的脚本运行统计的方法（需要 self 的 mysql 连接对象存在）
        super(AyuTwistedMysqlPipeline, self).close_spider(spider)
