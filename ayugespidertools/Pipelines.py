# Define your item pipelines here
#
# Don"t forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import pymysql
import warnings
import datetime
import dataclasses
from scrapy import Request
from retrying import retry
from pymysql import cursors
from enum import Enum, unique
from urllib.parse import urlparse
from twisted.enterprise import adbapi
from dbutils.pooled_db import PooledDB
from typing import Optional, Type, TypeVar
from twisted.internet import defer, reactor
from scrapy.pipelines.files import FilesPipeline
from ayugespidertools.common.Params import Param
from scrapy.pipelines.images import ImagesPipeline
from ayugespidertools.MongoClient import MongoDbBase
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Expend import MysqlErrorHandlingMixin


# 将 pymysql 中 Data truncated for column 警告类型置为 Error，其他警告忽略
warnings.filterwarnings("error", category=pymysql.Warning, message=".*Data truncated for column.*")


__all__ = [
    "AyuFtyMysqlPipeline",
    "AyuFtyMongoPipeline",
    "AyuTwistedMysqlPipeline",
    "AyuTurboMysqlPipeline",
    "AyuTwistedMongoPipeline",
]


TableEnumTypeVar = TypeVar("TableEnumTypeVar", bound="TableEnum")


@unique
class TableEnum(Enum):
    """
    数据库表枚举信息示例，用于限制存储信息类的字段及值不允许重复和修改
    """

    # 详情表示例信息
    demo_detail_table = {
        "value": "表名(eg: demo_detail)",
        "notes": "表注释信息(eg: 详情表信息)",
        "demand_code": "需求表对应数据(eg: Demo_detail_table_demand_code，此示例没有意义，需要自定义)"
    }


class AyuMysqlPipeline(MysqlErrorHandlingMixin):
    """
    Mysql 存储场景的 scrapy pipeline 扩展的主要功能示例
    """

    def __init__(
        self,
        table_prefix: str,
        table_enum: Type[TableEnumTypeVar],
        env: str,
        record_log_to_mysql: Optional[bool] = False
    ) -> None:
        """
        初始化 Mysql 链接所需要的信息
        Args:
            table_prefix: 数据库表前缀
            table_enum: 数据表的枚举信息
            env: 当前程序部署环境名
            record_log_to_mysql: 是否需要记录程序采集的基本信息到 Mysql 中
        """
        self.table_prefix = table_prefix
        self.table_enum = table_enum
        self.env = env
        self.record_log_to_mysql = record_log_to_mysql
        # 排序规则，用于创建数据库时使用
        self.collate = None
        self.mysql_config = None
        self.conn = None
        self.slog = None
        self.cursor = None
        self.crawl_time = datetime.date.today()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            # 数据库表前缀
            table_prefix=crawler.settings.get("MYSQL_TABLE_PREFIX", ""),
            # 数据库表枚举是否开启
            table_enum=crawler.settings.get("DATA_ENUM"),
            # 获取部署的环境
            env=crawler.settings.get("ENV"),
            # 当 record_log_to_mysql 为 True 时，会记录运行情况
            record_log_to_mysql=crawler.settings.get("RECORD_LOG_TO_MYSQL", False),
        )

    def open_spider(self, spider):
        self.slog = spider.slog
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)
        self.conn = self._connect(self.mysql_config)
        self.cursor = self.conn.cursor()

    def get_table_name(self, table: str) -> str:
        """
        组合完整的数据库表
        Args:
            table: 数据表的后缀

        Returns:
            1). 拼接成完整的数据表的值
        """
        full_table_name = f"{self.table_prefix}{table}"

        # 最终的数据表名不能含有空格
        assert " " not in full_table_name, "数据表名不能含空格，请检查 MYSQL_TABLE_PREFIX 参数和 item 中的 table 参数"
        return full_table_name

    def get_new_item(self, item):
        """
        重新整合 item
        Args:
            item: scrapy yield 的 item 信息

        Returns:
            1). 整合后的 item
        """
        new_item = {}
        notes_dic = {}
        # 如果是 ayugespidertools.Items 中的各个自封装类型时
        # alldata 可以认为是关键字，需要判断其是否存在，且是否为 dict。
        # 若其存在且为 dict，则默认其为 Items 中的 alldata 数据类型而非单一字段值
        insert_data = item.get("alldata")
        if all([insert_data, isinstance(insert_data, dict)]):
            # 如果是 Item 对象转化而来，则需要转换下，以便兼容写法
            for key, value in insert_data.items():
                if type(value) == dict:
                    new_item[key] = value.get("key_value", "")
                    notes_dic[key] = value["notes"]
                else:
                    new_item[key] = value
                    notes_dic[key] = key

        # 兼容旧写法，直接 dict 格式的 item 即可
        else:
            # 将存入表的无关字段给去掉
            save_data_item = ReuseOperation.get_items_except_keys(dict_config=item, key_list=["table", "item_mode"])
            for key, value in save_data_item.items():
                new_item[key] = value
                notes_dic[key] = key

        return {
            "new_item": new_item,
            "notes_dic": notes_dic
        }

    def process_item(self, item, spider):
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["item_mode"] == "Mysql":
            self.insert_item(self.get_new_item(item_dict), self.get_table_name(item_dict["table"]))
        return item

    def insert_item(self, item_o, table):
        """
        通用插入数据，将 item 数据存入 Mysql 中，item 中的 key 需要跟 Mysql 数据中的字段名称一致
        Args:
            item_o: item
            table: 数据库表名

        Returns:
            None
        """
        new_item = item_o.get("new_item")
        note_dic = item_o.get("notes_dic")
        keys = f"""`{"`, `".join(new_item.keys())}`"""
        values = ", ".join(["%s"] * len(new_item))
        update = ",".join([" `{key}` = %s".format(key=key) for key in new_item])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"

        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(new_item.values()) * 2):
                self.conn.commit()

        except Exception as e:
            self.slog.warning(f":{e}")
            self.slog.warning(f"Item:{new_item}  Table: {table}")
            self.conn.rollback()
            err_msg = str(e)
            if "1054" in err_msg:
                self.deal_1054_error(err_msg=err_msg, conn=self.conn, cursor=self.cursor, table=table, note_dic=note_dic)
                return self.insert_item(item_o, table)

            elif "1146" in err_msg:
                self.deal_1146_error(
                    err_msg=err_msg,
                    table_prefix=self.table_prefix,
                    cursor=self.cursor,
                    charset=self.mysql_config["charset"],
                    collate=self.collate,
                    table_enum=self.table_enum
                )
                self.insert_item(item_o, table)
            elif "1406" in err_msg:
                self.deal_1406_error(
                    err_msg=err_msg,
                    conn=self.conn,
                    cursor=self.cursor,
                    database=self.mysql_config["database"],
                    table=table,
                    note_dic=note_dic
                )

            elif "1265" in err_msg:
                self.deal_1265_error(
                    err_msg=err_msg,
                    conn=self.conn,
                    cursor=self.cursor,
                    database=self.mysql_config["database"],
                    table=table,
                    note_dic=note_dic
                )

            else:
                # 碰到其他的异常才打印错误日志，已处理的异常不打印
                self.slog.error(f"ERROR:{e}")

            try:
                self.conn.ping(reconnect=True)
            except Exception:
                self.conn = self._connect(self.mysql_config)
                self.cursor = self.conn.cursor()
                self.cursor.execute(sql, tuple(new_item.values()) * 2)
                self.slog.info(f"重新连接 db: =>{table}, =>{new_item} ")

    def close_spider(self, spider):
        # 是否记录程序采集的基本信息到 Mysql 中，只有打开 record_log_to_mysql 配置才会收集和存储相关的统计信息
        if self.record_log_to_mysql:
            log_info = self._get_log_by_spider(spider=spider, crawl_time=self.crawl_time)

            # 运行脚本统计信息
            self.insert_script_statistics(log_info)
            self.table_collection_statistics(spider_name=spider.name, database=spider.mysql_config["database"], crawl_time=self.crawl_time)

        if self.conn:
            self.conn.close()

    def table_collection_statistics(self, spider_name: str, database: str, crawl_time: datetime.date):
        """
        统计数据库入库数据，获取当前数据库中所有包含 crawl_time 字段的数据表的简要信息
        Args:
            spider_name: 爬虫脚本名称
            database: 数据库，保存程序采集记录保存的数据库
            crawl_time: 采集时间，程序运行时间

        Returns:
            None
        """
        sql = f'''
        select concat(
            'select "',
            TABLE_NAME,
            '", count(id) as num , crawl_time from ',
            TABLE_SCHEMA,
            '.',
            TABLE_NAME,
                ' where crawl_time = "{crawl_time}"'
        ) from information_schema.tables
        where TABLE_SCHEMA='{database}' and TABLE_NAME in (SELECT TABLE_NAME FROM information_schema.columns WHERE COLUMN_NAME='crawl_time');
        '''
        self.conn.ping(reconnect=True)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        if sql_list := [row[0] for row in results]:
            sql_all = " union all ".join(sql_list)
            self.cursor.execute(sql_all)
            results = self.cursor.fetchall()

            for row in results:
                table_statistics = {
                    "spider_name": spider_name,
                    "database": database,
                    "table_name": row[0],
                    "number": row[1],
                    "crawl_time": str((row[2] or crawl_time)),
                }
                self.insert_table_statistics(table_statistics)

    def insert_table_statistics(self, data: dict, table: Optional[str] = "table_collection_statistics"):
        """
        插入统计数据到表中
        Args:
            data: 需要统计的入库信息
            table: 存储表的名称

        Returns:
            None
        """
        self.conn.ping(reconnect=True)
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{table}` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `database` varchar(255) NOT NULL DEFAULT '-' COMMENT '采集程序和记录信息存储的数据库名',
            `spider_name` varchar(255) NOT NULL DEFAULT '-' COMMENT '脚本名称',            
            `crawl_time` datetime NOT NULL COMMENT '程序运行/数据采集时间',
            `table_name` varchar(255) NOT NULL COMMENT '此项目所在库（一般某个项目放在单独的数据库中）的当前表名',
            `number` varchar(255) NOT NULL COMMENT '当前表的当前 crawl_time 的采集个数',            
            PRIMARY KEY (`id`) USING BTREE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='项目对应库中各表采集统计表';
        """)

        keys = f"""`{"`, `".join(data.keys())}`"""
        values = ", ".join(["%s"] * len(data))
        update = ",".join([" `{key}` = %s".format(key=key) for key in data])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"
        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.slog.warning(f":{e}")

    @retry(stop_max_attempt_number=Param.retry_num, wait_random_min=Param.retry_time_min, wait_random_max=Param.retry_time_max)
    def insert_script_statistics(self, data: dict, table: Optional[str] = "script_collection_statistics"):
        """
        存储运行脚本的统计信息
        Args:
            data: 需要插入的 log 信息
            table: 存储表的名称

        Returns:
            None
        """
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{table}` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `database` varchar(255) NOT NULL DEFAULT '-' COMMENT '采集程序和记录信息存储的数据库名',
            `spider_name` varchar(255) NOT NULL DEFAULT '-' COMMENT '脚本名称',
            `uid` varchar(255) NOT NULL DEFAULT '-' COMMENT 'uid',
            `request_counts` varchar(255) NOT NULL DEFAULT '-' COMMENT '请求次数统计',
            `received_count` varchar(255) NOT NULL DEFAULT '-' COMMENT '接收次数统计',
            `item_counts` varchar(255) NOT NULL DEFAULT '-' COMMENT '采集数据量',
            `info_count` varchar(255) NOT NULL DEFAULT '-' COMMENT 'info 数据统计',
            `warning_count` varchar(255) NOT NULL DEFAULT '-' COMMENT '警告数据统计',
            `error_count` varchar(255) NOT NULL DEFAULT '-' COMMENT '错误数据统计',
            `start_time` datetime NOT NULL COMMENT '开始时间',
            `finish_time` datetime NOT NULL COMMENT '结束时间',
            `spend_minutes` varchar(255) NOT NULL DEFAULT '-' COMMENT '花费时间',
            `crawl_time` datetime NOT NULL COMMENT '程序运行/数据采集时间',
            `log_count_ERROR` varchar(255) DEFAULT NULL COMMENT '错误原因',
            PRIMARY KEY (`id`) USING BTREE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='项目运行脚本统计信息表';
        """)

        keys = f"""`{"`, `".join(data.keys())}`"""
        values = ", ".join(["%s"] * len(data))
        update = ",".join([" `{key}` = %s".format(key=key) for key in data])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"
        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.slog.warning(f":{e}")


class AyuStatsMysqlPipeline(AyuMysqlPipeline):
    """
    记录运行脚本统计信息的简单示例，不在生成中使用
    """
    def __init__(self, *args, **kwargs):
        super(AyuStatsMysqlPipeline, self).__init__(*args, **kwargs)

    def close_spider(self, spider):
        # 获取脚本运行状态信息中为 date 类型的数据，将其延时 8 小时处理
        text = {
            k.replace("/", "_"): (v + datetime.timedelta(hours=8)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if isinstance(v, datetime.datetime)
            else v
            for k, v in spider.stats.get_stats().items()
        }
        log_info = {
            "spider_name": spider.name,
            "request_counts": text.get("downloader_request_count"),
            "received_count": text.get("response_received_count"),
            "item_counts": text.get("item_scraped_count"),
            "info_count": text.get("log_count_INFO"),
            "warning_count": text.get("log_count_WARNING"),
            "error_count": text.get("log_count_ERROR"),
            "start_time": text.get("start_time"),
            "finish_time": datetime.datetime.now(),
            "spend_minutes": (datetime.datetime.now() - spider.stats.get_stats().get("start_time") - datetime.timedelta(hours=8)).seconds / 60,
            "table": "logs"
        }
        self.insert_item(self.get_new_item(log_info), self.get_table_name(log_info.get("table")))


class AyuFtyMysqlPipeline(AyuMysqlPipeline):
    """
    Mysql 存储场景的 scrapy pipeline 扩展
    """
    def __init__(self, *args, **kwargs):
        super(AyuFtyMysqlPipeline, self).__init__(*args, **kwargs)


class AyuTurboMysqlPipeline(AyuMysqlPipeline):
    """
    Mysql 存储场景的 scrapy pipeline 扩展，使用 dbutils.pooled_db 实现
    """

    def __init__(self, pool_db_config, *args, **kwargs):
        super(AyuTurboMysqlPipeline, self).__init__(*args, **kwargs)
        self.pool_db_config = pool_db_config

    @classmethod
    def from_crawler(cls, crawler):
        pool_db_config = crawler.settings.get('POOL_DB_CONFIG', None)
        return cls(
            # 数据库表前缀
            table_prefix=crawler.settings.get("MYSQL_TABLE_PREFIX", ""),
            # 数据库表枚举是否开启
            table_enum=crawler.settings.get("DATA_ENUM"),
            # 获取部署的环境
            env=crawler.settings.get("ENV"),
            # 当 record_log_to_mysql 为 True 时，会记录运行情况
            record_log_to_mysql=crawler.settings.get("RECORD_LOG_TO_MYSQL", False),

            # 数据库连接池配置
            pool_db_config=pool_db_config,
        )

    def open_spider(self, spider):
        self.slog = spider.slog
        if not self.pool_db_config:
            spider.slog.warning("未配置 POOL_DB_CONFIG 参数，将使用其默认参数")
            self.pool_db_config = {
                # 连接池允许的最大连接数
                'maxconnections': 5,
                # 连接池中空闲连接的最大数量。默认0，即无最大数量限制
                'maxcached': 0,
                # 连接的最大使用次数。默认0，即无使用次数限制
                'maxusage': 0,
                # 连接数达到最大时，新连接是否可阻塞。默认False，即达到最大连接数时，再取新连接将会报错
                'blocking': True,
            }
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。这个并不需要此连接对象，直接关闭即可
        self._connect(pymysql_dict_config=self.mysql_config).close()

        # 添加 PooledDB 的配置
        self.mysql_config.update(self.pool_db_config)
        self.conn = PooledDB(pymysql, **self.mysql_config).connection()
        self.cursor = self.conn.cursor()


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
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。
        # 记录日志时需要此连接对象，否则直接关闭
        if self.record_log_to_mysql:
            self.conn = self._connect(pymysql_dict_config=self.mysql_config)
            self.cursor = self.conn.cursor()
        else:
            self._connect(pymysql_dict_config=self.mysql_config).close()

        self.mysql_config['cursorclass'] = cursors.DictCursor
        self.dbpool = adbapi.ConnectionPool("pymysql", cp_reconnect=True, **self.mysql_config)
        query = self.dbpool.runInteraction(self.db_create)
        query.addErrback(self.db_create_err)

    def db_create(self, cursor):
        pass

    def db_create_err(self, failure):
        self.slog.error(f'创建数据表失败: {failure}')

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
        update = ",".join([" `{key}` = %s".format(key=key) for key in new_item])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"

        try:
            cursor.execute(sql, tuple(new_item.values()) * 2)

        except Exception as e:
            self.slog.warning(f":{e}")
            self.slog.warning(f"Item:{new_item}  Table: {table}")
            err_msg = str(e)
            if "1054" in err_msg:
                self.deal_1054_error(err_msg=err_msg, conn=None, cursor=cursor, table=table, note_dic=note_dic)
                return self.db_insert(cursor, item)

            elif "1146" in err_msg:
                self.deal_1146_error(
                    err_msg=err_msg,
                    table_prefix=self.table_prefix,
                    cursor=cursor,
                    charset=self.mysql_config["charset"],
                    collate=self.collate,
                    table_enum=self.table_enum
                )
                return self.db_insert(cursor, item)

            elif "1406" in err_msg:
                self.deal_1406_error(
                    err_msg=err_msg,
                    conn=None,
                    cursor=cursor,
                    database=self.mysql_config["database"],
                    table=table,
                    note_dic=note_dic
                )
                return self.db_insert(cursor, item)

            elif "1265" in err_msg:
                self.deal_1265_error(
                    err_msg=err_msg,
                    conn=None,
                    cursor=cursor,
                    database=self.mysql_config["database"],
                    table=table,
                    note_dic=note_dic
                )
                return self.db_insert(cursor, item)

            else:
                # 碰到其他的异常才打印错误日志，已处理的异常不打印
                self.slog.error(f"ERROR:{e}")

        return item

    def handle_error(self, failure, item):
        self.slog.error(f'插入数据失败:{failure}, item: {item}')

    def close_spider(self, spider):
        # 不删除 cursorclass 其实也不影响
        if "cursorclass" in self.mysql_config.keys():
            del self.mysql_config["cursorclass"]

        # 这里新建数据库链接，是为了正常继承父类的脚本运行统计的方法（需要 self 的 mysql 连接对象存在）
        super(AyuTwistedMysqlPipeline, self).close_spider(spider)


class FilesDownloadPipeline(FilesPipeline):
    """
    文件下载场景的 scrapy pipeline 扩展
    """

    def get_media_requests(self, item, info):
        if file_url := item.get("file_url"):
            return Request(file_url)
        print("No file_url")

    def item_completed(self, results, item, info):
        if file_paths := [x["path"] for ok, x in results if ok]:
            item["file_path"] = file_paths[0]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return f"files/{os.path.basename(urlparse(request.url).path)}"


class ImagesDownloadPipeline(ImagesPipeline):
    """
    图片下载场景的 scrapy pipeline 扩展
    """

    def get_media_requests(self, item, info):
        if image_url := item.get("image_url"):
            return Request(image_url)
        print("No image_url")

    def item_completed(self, results, item, info):
        if image_paths := [x["path"] for ok, x in results if ok]:
            item["image_path"] = image_paths[0]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return f"images/{os.path.basename(urlparse(request.url).path)}"


class AyuStatisticsMysqlPipeline(MysqlErrorHandlingMixin):
    """
    Mysql 存储且记录脚本运行状态的简单示例
    """

    def __init__(self, env):
        self.env = env
        self.slog = None
        self.conn = None
        self.cursor = None
        self.collate = None
        self.mysql_config = None
        self.crawl_time = datetime.date.today()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            env=crawler.settings.get("ENV", "")
        )

    def open_spider(self, spider):
        self.slog = spider.slog
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)

        self.conn = self._connect(self.mysql_config)
        self.cursor = self.conn.cursor()

    def insert(self, data_item, table):
        """
        插入数据
        Args:
            data_item: scrapy item
            table: 存储至 mysql 的表名

        Returns:
            None
        """
        data = dataclasses.asdict(data_item)
        keys = f"""`{"`, `".join(data.keys())}`"""
        values = ", ".join(["%s"] * len(data))
        update = ",".join([" `{key}` = %s".format(key=key) for key in data])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"
        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.conn.commit()
        except Exception as e:
            self.slog.warning(f":{e}")

    def close_spider(self, spider):
        log_info = self._get_log_by_spider(spider=spider, crawl_time=self.crawl_time)
        self.insert(log_info, "script_collection_statistics")

        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        return item


class AyuFtyMongoPipeline(MongoDbBase):
    """
    MongoDB 存储场景的 scrapy pipeline 扩展
    """

    def __init__(
        self,
        mongodb_config: dict,
        app_conf_manage: bool,
        collection_prefix: Optional[str] = ""
    ) -> None:
        """
        初始化 mongoDB 连接，正常的话会返回 mongoDB 的连接对象 `connect` 和 `db` 对象
        Args:
            mongodb_config: mongDB 的连接配置
            app_conf_manage: 应用配置管理是否开启，用于从 consul 中取值；
                只有当 app_conf_manage 开启且不存在本地配置 LOCAL_MONGODB_CONFIG 时，才会从 consul 中取值！
            collection_prefix: mongDB 存储集合的前缀，默认为空字符
        """
        assert any([mongodb_config, app_conf_manage]), "未配置 MongoDB 连接配置！"
        assert isinstance(collection_prefix, str), "mongoDB 所要存储的集合前缀名称需要是 str 格式！"

        self.collection_prefix = collection_prefix or ""
        self.mongodb_config = None
        # 优先从本地中取配置
        if mongodb_config:
            self.mongodb_config = ReuseOperation.dict_keys_to_lower(mongodb_config)
            super(AyuFtyMongoPipeline, self).__init__(**self.mongodb_config)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongodb_config=crawler.settings.get('LOCAL_MONGODB_CONFIG'),
            app_conf_manage=crawler.settings.get('APP_CONF_MANAGE'),
            collection_prefix=crawler.settings.get('MONGODB_COLLECTION_PREFIX', ''),
        )

    def open_spider(self, spider):
        if not self.mongodb_config:
            self.mongodb_config = ReuseOperation.dict_keys_to_lower(spider.mongodb_conf)
            super(AyuFtyMongoPipeline, self).__init__(**self.mongodb_config)

        # 用于输出日志
        if all([self.conn, self.db]):
            spider.slog.info(f"已连接至 host: {self.mongodb_config['host']}, database: {self.mongodb_config['database']} 的 MongoDB 目标数据库")

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        """
        mongoDB 存储的方法，item["mongo_update_rule"] 用于存储查询条件，如果查询数据存在的话就更新，不存在的话就插入；
        如果没有 mongo_update_rule 则每次都新增
        Args:
            item: scrapy item
            spider: scrapy spider

        Returns:
            item: scrapy item
        """
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["item_mode"] == "MongoDB":
            insert_data = item_dict.get("alldata")
            # 如果有 alldata 字段，则其为推荐格式
            if all([insert_data, isinstance(insert_data, dict)]):
                # 判断数据中中的 alldata 的格式：
                #     1.推荐：是嵌套 dict，就像 AyuMysqlPipeline 一样 -- 这是为了通用写法风格；
                #     2. 是单层的 dict
                # 如果是嵌套格式的话，需要再转化为正常格式，因为此场景不需要像 Mysql 一样依赖备注来生成字段注释
                if any(isinstance(v, dict) for v in insert_data.values()):
                    insert_data = {v: insert_data[v]["key_value"] for v in insert_data.keys()}

            # 否则为旧格式
            else:
                insert_data = ReuseOperation.get_items_except_keys(
                    dict_config=item_dict,
                    key_list=["table", "item_mode", "mongo_update_rule"])

            # 真实的集合名称为：集合前缀名 + 集合名称
            collection_name = f'''{self.collection_prefix}{item_dict["table"]}'''
            # 如果没有查重字段时，就直接插入数据（不去重）
            if not item_dict.get("mongo_update_rule"):
                self.db[collection_name].insert(insert_data)
            else:
                self.db[collection_name].update(item_dict["mongo_update_rule"], {'$set': insert_data}, True)
        return item


class AyuTwistedMongoPipeline(AyuFtyMongoPipeline):
    """
    使用 twisted 的 adbapi 实现 mongoDB 存储场景下的异步操作
    """

    def __init__(self, *args, **kwargs):
        super(AyuTwistedMongoPipeline, self).__init__(*args, **kwargs)

    def spider_closed(self, spider):
        if self.conn:
            self.conn.close()

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        out = defer.Deferred()
        reactor.callInThread(self.db_insert, item, out)
        yield out
        defer.returnValue(item)

    def db_insert(self, item, out):
        item_dict = ToolsForAyu.convert_items_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["item_mode"] == "MongoDB":
            insert_data = item_dict.get("alldata")
            # 如果有 alldata 字段，则其为推荐格式
            if all([insert_data, isinstance(insert_data, dict)]):
                if any(isinstance(v, dict) for v in insert_data.values()):
                    insert_data = {v: insert_data[v]["key_value"] for v in insert_data.keys()}

            # 否则为旧格式
            else:
                insert_data = ReuseOperation.get_items_except_keys(
                    dict_config=item_dict,
                    key_list=["table", "item_mode", "mongo_update_rule"])

            # 真实的集合名称为：集合前缀名 + 集合名称
            collection_name = f'''{self.collection_prefix}{item_dict["table"]}'''
            self.db[collection_name].update(item_dict["mongo_update_rule"], {'$set': insert_data}, True)
            reactor.callFromThread(out.callback, item_dict)
