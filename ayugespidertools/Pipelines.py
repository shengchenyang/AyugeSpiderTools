# Define your item pipelines here
#
# Don"t forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import re
import pymysql
import warnings
import datetime
import dataclasses
from scrapy import Request
from retrying import retry
from pymysql import cursors
from urllib.parse import urlparse
from twisted.enterprise import adbapi
from dbutils.pooled_db import PooledDB
from ayugespidertools.config import logger
from twisted.internet import defer, reactor
from scrapy.pipelines.files import FilesPipeline
from ayugespidertools.common.Params import Param
from scrapy.pipelines.images import ImagesPipeline
from ayugespidertools.MongoClient import MongoDbBase
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.common.MultiPlexing import ReuseOperation


# 将 pymysql 中 Data truncated for column 警告类型置为 Error，其他警告忽略
warnings.filterwarnings("error", category=pymysql.Warning, message=".*Data truncated for column.*")


__all__ = [
    "AyuFtyMysqlPipeline",
    "AyuFtyMongoPipeline",
    "AyuTwistedMysqlPipeline",
    "AyuTurboMysqlPipeline",
    "AyuTwistedMongoPipeline",
]


class AyuMysqlPipeline:
    """
    Mysql 存储场景的 scrapy pipeline 扩展的主要功能示例
    """

    def __init__(self, table_prefix, table_enum, env, record_log_to_mysql):
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

    def get_column_type(self, database, table, column) -> str:
        """
        获取数据字段存储类型
        Args:
            database: 数据库
            table: 数据表
            column: 字段名称

        Returns:
            column_type: 字段存储类型
        """
        sql = '''select COLUMN_TYPE from information_schema.columns where table_schema = '%s' and 
            table_name = '%s' and COLUMN_NAME= '%s';''' % (database, table, column)
        column_type = None
        try:
            self.conn.ping(reconnect=True)
            res = self.cursor.execute(sql)
            if res:
                # 注意，此处返回的结构示例为：(('varchar(10)',),)
                lines = self.cursor.fetchall()
                column_type = lines[0][0] if len(lines) == 1 else ""
        except Exception as e:
            logger.error(f"{e}")
        return column_type

    def create_table(self, table_name: str, tabel_notes: str = "", demand_code: str = ""):
        """
        创建数据库表
        Args:
            table_name: 创建表的名称
            tabel_notes: 创建表的注释
            demand_code: 创建表的需求对应的 code 值，用于和需求中的任务对应

        Returns:
            None
        """
        # 用于表格 comment 的参数生成(即 tabel_notes 参数)
        if demand_code != "":
            tabel_notes = demand_code + "_" + tabel_notes

        sql = '''CREATE TABLE `%s` (`id` int(32) NOT NULL AUTO_INCREMENT COMMENT 'id',
            PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET=%s COLLATE=%s COMMENT='%s'; ''' % (
            table_name, self.mysql_config["charset"], self.collate, tabel_notes)
        try:
            # 执行 sql 查询，获取数据
            data = self.cursor.execute(sql)
            if any([data == 0, not data]):
                logger.info(f"创建数据表 {tabel_notes}: {table_name} 成功！")

        except Exception as e:
            logger.error(f"创建表失败，tabel_notes：{tabel_notes}，table_name：{table_name}，error：{e}")

    @retry(stop_max_attempt_number=Param.retry_num, wait_random_min=Param.retry_time_min, wait_random_max=Param.retry_time_max)
    def _connect(self, pymysql_dict_config):
        try:
            self.conn = pymysql.connect(**pymysql_dict_config)
        except Exception as e:
            logger.warning(f"目标数据库：{pymysql_dict_config['database']} 不存在，尝试创建中...")
            if "1049" in str(e):
                # 如果连接目标数据库报不存在的错误时，先创建出此目标数据库
                ReuseOperation.create_database(pymysql_dict_config)
        else:
            # 连接没有问题就直接返回连接对象
            return self.conn
        # 出现数据库不存在问题后，在创建数据库 create_database 后，再次返回连接对象
        return pymysql.connect(**pymysql_dict_config)

    def open_spider(self, spider):
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)
        self.conn = self._connect(self.mysql_config)
        self.cursor = self.conn.cursor()

    def get_table_name(self, table):
        """
        组合完整的数据库表
        Args:
            table: 数据表的后缀

        Returns:
            1). 拼接成完整的数据表的值
        """
        return self.table_prefix + table

    def get_new_item(self, item):
        """
        重新整合 item
        Args:
            item: scrapy yield 的 item 信息

        Returns:
            1). 整合后的 item
        """
        new_item = dict()
        notes_dic = dict()
        # 如果是 ayugespidertools.Items 中的各个自封装类型时
        if item.get("alldata"):
            # 如果是 Item 对象转化而来，则需要转换下，以便兼容写法
            for key, value in item["alldata"].items():
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
            for k, v in save_data_item.items():
                key = k.strip()
                # 将存入表的无关字段给去掉
                if isinstance(v, str):
                    new_item[key] = v.strip()
                    notes_dic[key] = key
                else:
                    new_item[key] = v
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
        keys = "`" + "`, `".join(new_item.keys()) + "`"
        values = ", ".join(["%s"] * len(new_item))
        sql = """INSERT INTO {table} ({keys}) values ({values}) ON DUPLICATE KEY UPDATE """.format(table=table,keys=keys, values=values)
        update = ",".join([" `{key}` = %s".format(key=key) for key in new_item])
        sql += update

        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(new_item.values()) * 2):
                self.conn.commit()

        except Exception as e:
            logger.warning(f":{e}")
            logger.warning(f"Item:{new_item}  Table: {table}")
            self.conn.rollback()
            patern_colum = re.compile(r"Unknown column '(.*?)' in 'field list'")
            if "1054" in str(e):
                text = re.findall(patern_colum, str(e))
                colum = text[0]
                notes = note_dic[colum]

                if colum == "url":
                    sql = "ALTER TABLE `%s` ADD COLUMN `%s` TEXT(500) NULL COMMENT '%s';" % (table, colum, notes)
                elif colum in ["create_time", "crawl_time"]:
                    sql = "ALTER TABLE `%s` ADD COLUMN `%s` DATE NULL DEFAULT NULL COMMENT '%s';" % (table, colum, notes)
                else:
                    sql = "ALTER TABLE `%s` ADD COLUMN `%s` VARCHAR(190) NULL DEFAULT '' COMMENT '%s';" % (table, colum, notes)

                try:
                    self.conn.ping(reconnect=True)
                    if self.cursor.execute(sql):
                        self.conn.commit()
                except Exception as e:
                    if "1060" in str(e):
                        logger.info(f"添加字段 {colum} 已存在")
                    else:
                        logger.info(f"{e}")
                return self.insert_item(item_o, table)

            elif "1146" in str(e):
                patern_table = re.compile(r"Table '(.*?)' doesn't exist")
                text = re.findall(patern_table, str(e))
                table = text[0].split(".")[1]

                # 写入表枚举
                have_create_flag = False
                if self.table_enum:
                    for name, member in self.table_enum.__members__.items():
                        table_name = self.table_prefix + member.value.get("value", "")
                        table_notes = member.value.get("notes", "")
                        demand_code = member.value.get("demand_code", "")
                        if table_name == table:
                            have_create_flag = True
                            self.create_table(table_name, table_notes, demand_code)
                            break
                        else:
                            continue

                    if have_create_flag is False:
                        self.create_table(table)

                    self.insert_item(item_o, table)
                else:
                    # 未定义 Tabel_Enum 则建表
                    logger.info("未定义数据库表枚举，进行创表操作")
                    table_name = table
                    self.create_table(table_name)
                    self.insert_item(item_o, table)

            elif "1406" in str(e):
                if "Data too long for" in str(e):
                    patern_colum = re.compile(r"Data too long for column '(.*?)' at")
                    text = re.findall(patern_colum, str(e))
                    colum = text[0]
                    notes = note_dic[colum]
                    column_type = self.get_column_type(database=self.mysql_config["database"], table=table, column=colum)
                    change_colum_type = "TEXT"
                    if "text" == column_type:
                        change_colum_type = "LONGTEXT"

                    sql = """ALTER TABLE `%s` CHANGE COLUMN `%s` `%s` %s NULL DEFAULT NULL COMMENT "%s" ;""" % (
                        table, colum, colum, change_colum_type, notes)

                    try:
                        self.conn.ping(reconnect=True)
                        if self.cursor.execute(sql):
                            self.conn.commit()
                    except Exception as e:
                        logger.info(f"更新字段类型失败 {e}")
                    return self.insert_item(item_o, table)
                else:
                    logger.info("1406 错误其他类型")

            elif "1265" in str(e):
                if "Data truncated for column" in str(e):
                    patern_colum = re.compile(r"Data truncated for column '(.*?)' at")
                    text = re.findall(patern_colum, str(e))
                    colum = text[0]
                    notes = note_dic[colum]
                    column_type = self.get_column_type(database=self.mysql_config["database"], table=table, column=colum)
                    change_colum_type = "TEXT"
                    if "text" == column_type:
                        change_colum_type = "LONGTEXT"

                    sql = """ALTER TABLE `%s` CHANGE COLUMN `%s` `%s` %s NULL DEFAULT NULL COMMENT "%s" ;""" % (
                        table, colum, colum, change_colum_type, notes)
                    try:
                        self.conn.ping(reconnect=True)
                        if self.cursor.execute(sql):
                            self.conn.commit()
                    except Exception as e:
                        logger.info(f"更新字段类型失败 {e}")
                    return self.insert_item(item_o, table)
                else:
                    logger.info("1265 错误其他类型")

            else:
                # 碰到其他的异常才打印错误日志，已处理的异常不打印
                logger.error(f"ERROR:{e}")

            try:
                self.conn.ping(reconnect=True)
            except Exception:
                self.conn = self._connect(self.mysql_config)
                self.cursor = self.conn.cursor()
                self.cursor.execute(sql, tuple(new_item.values()) * 2)
                logger.info(f"重新连接 db: =>{table}, =>{new_item} ")

    def close_spider(self, spider):
        mysql_config = spider.mysql_config
        text = {}
        stats = spider.stats.get_stats()
        error_reason = ""
        for k, v in stats.items():
            if isinstance(v, datetime.datetime):
                text[k.replace("/", "_")] = (v + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                if "response_status_count" in k and k != "downloader/response_status_count/200":
                    status_code = k.split("/")[-1] if len(k.split("/")) > 0 else ""
                    if status_code.startswith("4"):
                        if status_code == "429":
                            error_reason += "%s错误：代理超过使用频率限制 " % status_code
                        else:
                            error_reason += "%s错误：网页失效/无此网页/网站拒绝访问 " % status_code
                    elif status_code.startswith("5"):
                        error_reason += "%s错误：网站服务器处理出错 " % status_code
                    elif status_code != "":
                        error_reason += "%s:待人工排查原因" % status_code
                elif "exception_type_count" in k:
                    error_name = k.split("/")[-1]
                    if "Timeout" in error_name:
                        error_reason += "%s:网站响应超时错误 " % error_name
                    elif "ConnectionDone" in error_name:
                        error_reason += "%s:网站与脚本连接断开 " % error_name
                    elif "ResponseNeverReceived" or "ResponseFailed" in error_name:
                        error_reason += "%s:网站无响应 " % error_name
                    else:
                        error_reason += "%s:待人工排查原因" % error_name

                text[k.replace("/", "_")] = v
        log_info = {
            "database": mysql_config["database"],
            # 脚本名称
            "spider_name": spider.name,
            # uid
            "uid": mysql_config["database"] + "|" + spider.name,
            # 请求次数统计
            "request_counts": text.get("downloader_request_count", 0),
            # 接收次数统计
            "received_count": text.get("response_received_count", 0),
            # 采集数据量
            "item_counts": text.get("item_scraped_count", 0),
            # info 数据统计
            "info_count": text.get("log_count_INFO", 0),
            # 警告数据统计
            "warning_count": text.get("log_count_WARNING", 0),
            # 错误数据统计
            "error_count": text.get("log_count_ERROR", 0),
            # 开始时间
            "start_time": text.get("start_time"),
            # 结束时间
            "finish_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # 花费时间
            "spend_minutes": round((datetime.datetime.now() - stats.get("start_time") - datetime.timedelta(hours=8)).seconds / 60, 2),
            "crawl_time": self.crawl_time
        }

        # 错误原因
        if text.get("log_count_ERROR", 0):
            log_info["log_count_ERROR"] = error_reason if error_reason else "请人工排查错误原因！"

        else:
            log_info["log_count_ERROR"] = ""

        # 是否记录程序采集的基本信息到 Mysql 中
        if self.record_log_to_mysql:
            # 运行脚本统计信息
            self.insert_script_statistics(log_info)
            self.table_collection_statistics(spider_name=spider.name, database=mysql_config["database"], crawl_time=self.crawl_time)

        self.conn.close()

    def table_collection_statistics(self, spider_name: str, database: str, crawl_time: datetime.date):
        """
        统计数据库入库数据
        Args:
            spider_name: 爬虫脚本名称
            database: 数据库，保存程序采集记录保存的数据库
            crawl_time: 采集时间，程序运行时间

        Returns:
            None
        """
        sql = '''
        select concat(
            'select "',
            TABLE_name,
            '", count(id) as num , crawl_time from ',
            TABLE_SCHEMA,
            '.',
            TABLE_name,
                ' where crawl_time = "%s"'
        ) from information_schema.tables
        where TABLE_SCHEMA='%s';
        ''' % (crawl_time, database)
        table_statistics_list = []
        self.conn.ping(reconnect=True)
        self.cursor.execute(sql)
        # 获取所有记录列表
        results = self.cursor.fetchall()
        sql_list = []
        for row in results:
            sql_list.append(row[0])

        sql_all = " union all ".join(sql_list)
        self.cursor.execute(sql_all)
        results = self.cursor.fetchall()
        for row in results:
            table_statistics = dict()
            table_statistics["spider_name"] = spider_name
            table_statistics["database"] = database
            table_statistics["table_name"] = row[0]
            table_statistics["number"] = row[1]
            table_statistics["crawl_time"] = str(row[2] or crawl_time)
            table_statistics_list.append(table_statistics)
            self.insert_table_statistics(table_statistics)

    def insert_table_statistics(self, data_item):
        """
        插入统计数据到表中
        Args:
            data_item: 需要统计的入库信息

        Returns:
            None
        """
        table = "table_collection_statistics"
        self.conn.ping(reconnect=True)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS `{}` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `database` varchar(255) NOT NULL DEFAULT '-' COMMENT '采集程序和记录信息存储的数据库名',
            `spider_name` varchar(255) NOT NULL DEFAULT '-' COMMENT '脚本名称',            
            `crawl_time` datetime NOT NULL COMMENT '程序运行/数据采集时间',
            `table_name` varchar(255) NOT NULL COMMENT '此项目所在库（一般某个项目放在单独的数据库中）的当前表名',
            `number` varchar(255) NOT NULL COMMENT '当前表的当前 crawl_time 的采集个数',            
            PRIMARY KEY (`id`) USING BTREE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='项目对应库中各表采集统计表';
        """.format(table))

        data = dict(data_item)
        keys = "`" + "`, `".join(data.keys()) + "`"
        values = ", ".join(["%s"] * len(data))
        sql = "INSERT INTO {table} ({keys}) values ({values}) ON DUPLICATE KEY UPDATE ".format(table=table, keys=keys, values=values)
        update = ",".join([" `{key}` = %s".format(key=key) for key in data])
        sql += update

        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.warning(f":{e}")

    @retry(stop_max_attempt_number=Param.retry_num, wait_random_min=Param.retry_time_min, wait_random_max=Param.retry_time_max)
    def insert_script_statistics(self, data_item):
        """
        存储运行脚本的统计信息
        Args:
            data_item: 需要插入的 log 信息

        Returns:
            None
        """
        table = "script_collection_statistics"
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS `{}` (
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
        """.format(table))

        data = dict(data_item)
        keys = "`" + "`, `".join(data.keys()) + "`"
        values = ", ".join(["%s"] * len(data))
        sql = "INSERT INTO {table} ({keys}) values ({values}) ON DUPLICATE KEY UPDATE ".format(table=table, keys=keys, values=values)
        update = ",".join([" `{key}` = %s".format(key=key) for key in data])
        sql += update
        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.warning(f":{e}")


class AyuStatsMysqlPipeline(AyuMysqlPipeline):
    """
    记录运行脚本统计信息的简单示例，不在生成中使用
    """
    def __init__(self, *args, **kwargs):
        super(AyuStatsMysqlPipeline, self).__init__(*args, **kwargs)

    def close_spider(self, spider):
        text = {}
        for k, v in spider.stats.get_stats().items():
            if isinstance(v, datetime.datetime):
                text[k.replace("/", "_")] = (v + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                text[k.replace("/", "_")] = v

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
        if not pool_db_config:
            logger.warning("未配置 POOL_DB_CONFIG 参数，将使用其默认参数")
            pool_db_config = {
                # 连接池允许的最大连接数
                'maxconnections': 5,
                # 连接池中空闲连接的最大数量。默认0，即无最大数量限制
                'maxcached': 0,
                # 连接的最大使用次数。默认0，即无使用次数限制
                'maxusage': 0,
                # 连接数达到最大时，新连接是否可阻塞。默认False，即达到最大连接数时，再取新连接将会报错
                'blocking': True,
            }

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
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。这个并不需要此连接对象，直接关闭即可
        super()._connect(pymysql_dict_config=self.mysql_config).close()

        # 添加 PooledDB 的配置
        self.mysql_config.update(self.pool_db_config)
        self.conn = PooledDB(pymysql, **self.mysql_config).connection()
        # mark 为 True，查询 sql 返回字典格式数据
        # self.cursor = self.conn.cursor(pymysql.cursors.DictCursor) if self.mark else self.conn.cursor()
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
        # 用于建表时使用
        self.collate = None
        self.conn = None
        self.cursor = None

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
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_config=self.mysql_config)

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。且需要此连接对象，不能直接关闭
        self.conn = super()._connect(pymysql_dict_config=self.mysql_config)
        self.cursor = self.conn.cursor()

        self.mysql_config['cursorclass'] = cursors.DictCursor
        self.dbpool = adbapi.ConnectionPool("pymysql", cp_reconnect=True, **self.mysql_config)
        query = self.dbpool.runInteraction(self.db_create)
        query.addErrback(self.db_create_err)

    def db_create(self, cursor):
        pass

    def db_create_err(self, failure):
        logger.error('创建数据表失败: {}'.format(failure))

    def get_column_type_by_myself(self, cursor, database, table, column) -> str:
        """
        获取数据字段存储类型
        Args:
            cursor: cursor
            database: 数据库
            table: 数据表
            column: 字段名称

        Returns:
            column_type: 字段存储类型
        """
        sql = '''select COLUMN_TYPE from information_schema.columns where table_schema = '%s' and 
            table_name = '%s' and COLUMN_NAME= '%s';''' % (database, table, column)
        column_type = None
        try:
            res = cursor.execute(sql)
            if res:
                # 注意，此处返回的结构示例为：[{'COLUMN_TYPE': 'varchar(190)'}]
                lines = cursor.fetchall()
                column_type = lines[0]["COLUMN_TYPE"] if len(lines) == 1 else ""
        except Exception as e:
            logger.error(f"{e}")
        return column_type

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
        keys = "`" + "`, `".join(new_item.keys()) + "`"
        values = ", ".join(["%s"] * len(new_item))
        sql = """INSERT INTO {table} ({keys}) values ({values}) ON DUPLICATE KEY UPDATE """.format(table=table, keys=keys, values=values)
        update = ",".join([" `{key}` = %s".format(key=key) for key in new_item])
        sql += update

        try:
            cursor.execute(sql, tuple(new_item.values()) * 2)

        except Exception as e:
            logger.warning(f":{e}")
            logger.warning(f"Item:{new_item}  Table: {table}")
            # self.conn.rollback()
            patern_colum = re.compile(r"Unknown column '(.*?)' in 'field list'")
            if "1054" in str(e):
                text = re.findall(patern_colum, str(e))
                colum = text[0]
                notes = note_dic[colum]

                if colum == "url":
                    sql = "ALTER TABLE `%s` ADD COLUMN `%s` TEXT(500) NULL COMMENT '%s';" % (table, colum, notes)
                elif colum in ["create_time", "crawl_time"]:
                    sql = "ALTER TABLE `%s` ADD COLUMN `%s` DATE NULL DEFAULT NULL COMMENT '%s';" % (table, colum, notes)
                else:
                    sql = "ALTER TABLE `%s` ADD COLUMN `%s` VARCHAR(190) NULL DEFAULT '' COMMENT '%s';" % (table, colum, notes)

                try:
                    cursor.execute(sql)
                except Exception as e:
                    if "1060" in str(e):
                        logger.info(f"添加字段 {colum} 已存在")
                    else:
                        logger.info(f"{e}")
                return self.db_insert(cursor, item)

            elif "1146" in str(e):
                patern_table = re.compile(r"Table '(.*?)' doesn't exist")
                text = re.findall(patern_table, str(e))
                table = text[0].split(".")[1]

                # 写入表枚举
                have_create_flag = False
                if self.table_enum:
                    for name, member in self.table_enum.__members__.items():
                        table_name = self.table_prefix + member.value.get("value", "")
                        table_notes = member.value.get("notes", "")
                        demand_code = member.value.get("demand_code", "")
                        if table_name == table:
                            have_create_flag = True
                            super(AyuTwistedMysqlPipeline, self).create_table(table_name, table_notes, demand_code)
                            break
                        else:
                            continue

                    if have_create_flag is False:
                        super(AyuTwistedMysqlPipeline, self).create_table(table)

                    self.db_insert(cursor, item)
                else:
                    # 未定义 Tabel_Enum 则建表
                    logger.info("未定义数据库表枚举，进行创表操作")
                    table_name = table
                    super(AyuTwistedMysqlPipeline, self).create_table(table_name)
                    self.db_insert(cursor, item)

            elif "1406" in str(e):
                if "Data too long for" in str(e):
                    patern_colum = re.compile(r"Data too long for column '(.*?)' at")
                    text = re.findall(patern_colum, str(e))
                    colum = text[0]
                    notes = note_dic[colum]
                    column_type = self.get_column_type_by_myself(cursor=cursor, database=self.mysql_config["database"], table=table, column=colum)
                    change_colum_type = "TEXT"
                    if "text" == column_type:
                        change_colum_type = "LONGTEXT"

                    sql = """ALTER TABLE `%s` CHANGE COLUMN `%s` `%s` %s NULL DEFAULT NULL COMMENT "%s" ;""" % (table, colum, colum, change_colum_type, notes)

                    try:
                        cursor.execute(sql)
                    except Exception as e:
                        logger.info(f"更新字段类型失败 {e}")
                    return self.db_insert(cursor, item)
                else:
                    logger.info("1406 错误其他类型")

            elif "1265" in str(e):
                if "Data truncated for column" in str(e):
                    patern_colum = re.compile(r"Data truncated for column '(.*?)' at")
                    text = re.findall(patern_colum, str(e))
                    colum = text[0]
                    notes = note_dic[colum]
                    column_type = self.get_column_type_by_myself(cursor=cursor, database=self.mysql_config["database"], table=table, column=colum)
                    change_colum_type = "TEXT"
                    if "text" == column_type:
                        change_colum_type = "LONGTEXT"

                    sql = """ALTER TABLE `%s` CHANGE COLUMN `%s` `%s` %s NULL DEFAULT NULL COMMENT "%s" ;""" % (table, colum, colum, change_colum_type, notes)
                    try:
                        cursor.execute(sql)
                    except Exception as e:
                        logger.info(f"更新字段类型失败 {e}")
                    return self.db_insert(cursor, item)
                else:
                    logger.info("1265 错误其他类型")

            else:
                # 碰到其他的异常才打印错误日志，已处理的异常不打印
                logger.error(f"ERROR:{e}")

        return item

    def handle_error(self, failure, item):
        logger.error('插入数据失败:{}, item: {}'.format(failure, item))

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
        file_url = item.get("file_url")
        if file_url:
            return Request(file_url)
        logger.info("No file_url")

    def item_completed(self, results, item, info):
        file_paths = [x["path"] for ok, x in results if ok]
        if file_paths:
            item["file_path"] = file_paths[0]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return "files/" + os.path.basename(urlparse(request.url).path)


class ImagesDownloadPipeline(ImagesPipeline):
    """
    图片下载场景的 scrapy pipeline 扩展
    """

    def get_media_requests(self, item, info):
        image_url = item.get("image_url")
        if image_url:
            return Request(image_url)
        logger.info("No image_url")

    def item_completed(self, results, item, info):
        image_paths = [x["path"] for ok, x in results if ok]
        if image_paths:
            item["image_path"] = image_paths[0]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return "images/" + os.path.basename(urlparse(request.url).path)


class AyuStatisticsMysqlPipeline:
    """
    Mysql 存储且记录脚本运行状态的简单示例
    """

    def __init__(self, env):
        self.env = env
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

    @retry(stop_max_attempt_number=Param.retry_num, wait_random_min=Param.retry_time_min, wait_random_max=Param.retry_time_max)
    def _connect(self, pymysql_dict_config):
        try:
            self.conn = pymysql.connect(**pymysql_dict_config)
        except Exception as e:
            logger.warning(f"目标数据库：{pymysql_dict_config['database']} 不存在，尝试创建中...")
            if "1049" in str(e):
                ReuseOperation.create_database(pymysql_dict_config)
        else:
            # 连接没有问题就直接返回连接对象
            return self.conn
        # 出现数据库不存在问题后，在创建数据库 create_database 后，再次返回连接对象
        return pymysql.connect(**pymysql_dict_config)

    def open_spider(self, spider):
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
        # data = dict(data_item)
        data = dataclasses.asdict(data_item)
        keys = "`" + "`, `".join(data.keys()) + "`"
        values = ", ".join(["%s"] * len(data))
        sql = "INSERT INTO {table} ({keys}) values ({values}) ON DUPLICATE KEY UPDATE ".format(table=table, keys=keys, values=values)
        update = ",".join([" `{key}` = %s".format(key=key) for key in data])
        sql += update
        try:
            self.conn.ping(reconnect=True)
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.conn.commit()
        except Exception as e:
            logger.warning(f":{e}")

    def close_spider(self, spider):
        mysql_config = spider.mysql_config

        text = {}
        stats = spider.stats.get_stats()
        error_reason = ""
        for k, v in stats.items():
            if isinstance(v, datetime.datetime):
                text[k.replace("/", "_")] = (v + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                if "response_status_count" in k and k != "downloader/response_status_count/200":
                    status_code = k.split("/")[-1]
                    if status_code.startswith("4"):
                        if status_code == "429":
                            error_reason += "%s错误：代理超过使用频率限制 " % status_code
                        else:
                            error_reason += "%s错误：网页失效/无此网页/网站拒绝访问 " % status_code
                    elif status_code.startswith("5"):
                        error_reason += "%s错误：网站服务器处理出错 " % status_code
                    else:
                        error_reason += "%s:待人工排查原因" % status_code
                elif "exception_type_count" in k:
                    error_name = k.split("/")[-1]
                    if "Timeout" in error_name:
                        error_reason += "%s:网站响应超时错误 " % error_name
                    elif "ConnectionDone" in error_name:
                        error_reason += "%s:网站与脚本连接断开 " % error_name
                    elif "ResponseNeverReceived" or "ResponseFailed" in error_name:
                        error_reason += "%s:网站无响应 " % error_name
                    else:
                        error_reason += "%s:待人工排查原因" % error_name

                text[k.replace("/", "_")] = v
        log_info = {
            "database": mysql_config["database"],
            # 脚本名称
            "spider_name": spider.name,
            # uid
            "uid": mysql_config["database"] + "|" + spider.name,
            # 请求次数统计
            "request_counts": text.get("downloader_request_count", 0),
            # 接收次数统计
            "received_count": text.get("response_received_count", 0),
            # 采集数据量
            "item_counts": text.get("item_scraped_count", 0),
            # info 数据统计
            "info_count": text.get("log_count_INFO", 0),
            # 警告数据统计
            "warning_count": text.get("log_count_WARNING", 0),
            # 错误数据统计
            "error_count": text.get("log_count_ERROR", 0),
            # 开始时间
            "start_time": text.get("start_time"),
            # 结束时间
            "finish_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # 花费时间
            "spend_minutes": round((datetime.datetime.now() - stats.get("start_time") - datetime.timedelta(hours=8)).seconds / 60, 2),
            "crawl_time": self.crawl_time
        }

        if text.get("log_count_ERROR", 0):
            # 错误原因
            log_info["log_count_ERROR"] = error_reason if error_reason else "请人工排查错误原因！"

        else:
            log_info["log_count_ERROR"] = ""

        if self.env == "prod":
            self.insert(log_info, "script_collection_statistics")

        self.conn.close()

    def process_item(self, item, spider):
        return item


class AyuFtyMongoPipeline(MongoDbBase):
    """
    MongoDB 存储场景的 scrapy pipeline 扩展
    """

    def __init__(self, mongodb_config: dict, app_conf_manage: bool):
        """
        初始化 mongoDB 连接，正常的话会返回 mongoDB 的连接对象 `connect` 和 `db` 对象
        Args:
            mongodb_config: mongDB 的连接配置
        """
        assert all([mongodb_config, app_conf_manage]), "未配置 MongoDB 连接配置！"

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
        )

    def open_spider(self, spider):
        if not self.mongodb_config:
            self.mongodb_config = ReuseOperation.dict_keys_to_lower(spider.mongodb_conf)
            super(AyuFtyMongoPipeline, self).__init__(**self.mongodb_config)

        # 用于输出日志
        if all([self.conn, self.db]):
            logger.info(f"已连接至 host: {self.mongodb_config['host']}, database: {self.mongodb_config['database']} 的 MongoDB 目标数据库")

    def close_spider(self, spider):
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
            if insert_data:
                # 判断数据中中的 alldata 的格式：(1.推荐：是嵌套 dict，就像 AyuMysqlPipeline 一样 -- 这是为了通用写法风格；2. 是单层的 dict)
                # 如果是嵌套格式的话，需要再转化为正常格式，因为此场景不需要像 Mysql 一样依赖备注来生成字段注释
                if any([isinstance(v, dict) for v in insert_data.values()]):
                    insert_data = {v: insert_data[v]["key_value"] for v in insert_data.keys()}

            # 否则为旧格式
            else:
                insert_data = ReuseOperation.get_items_except_keys(dict_config=item_dict, key_list=["table", "item_mode", "mongo_update_rule"])

            # 如果没有查重字段时，就直接插入数据（不去重）
            if not item_dict.get("mongo_update_rule"):
                self.db[item_dict["table"]].insert(insert_data)
            else:
                self.db[item_dict["table"]].update(item_dict["mongo_update_rule"], {'$set': dict(insert_data)}, True)
        return item


class AyuTwistedMongoPipeline(AyuFtyMongoPipeline):
    """
    使用 twisted 的 adbapi 实现 mongoDB 存储场景下的异步操作
    """

    def __init__(self, *args, **kwargs):
        super(AyuTwistedMongoPipeline, self).__init__(*args, **kwargs)

    def spider_closed(self, spider):
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
            if insert_data:
                if any([isinstance(v, dict) for v in insert_data.values()]):
                    insert_data = {v: insert_data[v]["key_value"] for v in insert_data.keys()}

            # 否则为旧格式
            else:
                insert_data = ReuseOperation.get_items_except_keys(dict_config=item_dict, key_list=["table", "item_mode", "mongo_update_rule"])

            self.db[item_dict["table"]].update(item_dict["mongo_update_rule"], {'$set': dict(insert_data)}, True)
            reactor.callFromThread(out.callback, item_dict)
