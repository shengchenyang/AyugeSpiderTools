import datetime
import warnings
from typing import Any, Dict, Optional, Tuple, Type

import pymysql
from retrying import retry

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.mysqlerrhandle import Synchronize, deal_mysql_err
from ayugespidertools.common.params import Param
from ayugespidertools.common.typevars import AlterItem, MysqlConfig, TableEnumTypeVar
from ayugespidertools.common.utils import ToolsForAyu

# 将 pymysql 中 Data truncated for column 警告类型置为 Error，其他警告忽略
warnings.filterwarnings(
    "error", category=pymysql.Warning, message=".*Data truncated for column.*"
)

__all__ = [
    "AyuMysqlPipeline",
]


class AyuMysqlPipeline(MysqlPipeEnhanceMixin):
    """
    Mysql 存储场景的 scrapy pipeline 扩展的主要功能示例
    """

    def __init__(
        self,
        table_prefix: str,
        table_enum: Type[TableEnumTypeVar],
        env: str,
        record_log_to_mysql: Optional[bool] = False,
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
        self.mysql_conf: Optional[MysqlConfig] = None
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
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"

        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=self.mysql_conf)
        self.conn = self._connect(self.mysql_conf)
        self.cursor = self.conn.cursor()

    def get_table_name(self, table: str) -> str:
        """
        组合完整的数据库表
        Args:
            table: 数据表的后缀

        Returns:
            1). 拼接成完整的数据表的值
        """
        assert isinstance(table, str), "item 中 table 字段不是 str，或未传入 table 参数"
        full_table_name = f"{self.table_prefix}{table}"

        # 最终的数据表名不能含有空格
        assert (
            " " not in full_table_name
        ), "数据表名不能含空格，请检查 MYSQL_TABLE_PREFIX 参数和 item 中的 table 参数"
        return full_table_name

    def get_new_item(self, item_dict: Dict[str, Any]) -> AlterItem:
        """
        重新整合 item
        Args:
            item_dict: dict 类型的 item

        Returns:
            1). 整合后的 item
        """
        new_item = {}
        notes_dic = {}

        insert_data = ReuseOperation.get_items_except_keys(
            dict_conf=item_dict, key_list=["_item_mode", "_table"]
        )
        judge_item = next(iter(insert_data.values()))
        # 是 namedtuple 类型
        if ReuseOperation.is_namedtuple_instance(judge_item):
            for key, value in insert_data.items():
                new_item[key] = value.key_value
                notes_dic[key] = value.notes
        # 是普通的 dict 类型
        else:
            for key, value in insert_data.items():
                new_item[key] = value
                notes_dic[key] = ""

        return AlterItem(new_item=new_item, notes_dic=notes_dic)

    def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        # 先查看存储场景是否匹配
        if item_dict["_item_mode"] == "Mysql":
            self.insert_item(
                alter_item=self.get_new_item(item_dict),
                table=self.get_table_name(item_dict["_table"]),
            )
        return item

    def insert_item(self, alter_item: AlterItem, table: str):
        """
        通用插入数据，将 item 数据存入 Mysql 中，item 中的 key 需要跟 Mysql 数据中的字段名称一致
        Args:
            alter_item: 经过转变后的 item
            table: 数据库表名

        Returns:
            None
        """
        if not (new_item := alter_item.new_item):
            return

        note_dic = alter_item.notes_dic
        sql = self._get_sql_by_item(table=table, item=new_item)

        try:
            if self.cursor.execute(sql, tuple(new_item.values()) * 2):
                self.conn.commit()

        except Exception as e:
            self.slog.warning(f":{e}")
            self.slog.warning(f"Item:{new_item}  Table: {table}")
            self.conn.rollback()
            deal_mysql_err(
                Synchronize(),
                err_msg=str(e),
                conn=self.conn,
                cursor=self.cursor,
                charset=self.mysql_conf.charset,
                collate=self.collate,
                database=self.mysql_conf.database,
                table=table,
                table_prefix=self.table_prefix,
                table_enum=self.table_enum,
                note_dic=note_dic,
            )
            return self.insert_item(alter_item, table)

    def close_spider(self, spider):
        # 是否记录程序采集的基本信息到 Mysql 中，只有打开 record_log_to_mysql 配置才会收集和存储相关的统计信息
        if self.record_log_to_mysql:
            log_info = self._get_log_by_spider(
                spider=spider, crawl_time=self.crawl_time
            )

            # 运行脚本统计信息
            self.insert_script_statistics(log_info)
            self.table_collection_statistics(
                spider_name=spider.name,
                database=spider.mysql_conf.database,
                crawl_time=self.crawl_time,
            )

        if self.conn:
            self.conn.close()

    def table_collection_statistics(
        self, spider_name: str, database: str, crawl_time: datetime.date
    ):
        """
        统计数据库入库数据，获取当前数据库中所有包含 crawl_time 字段的数据表的简要信息
        Args:
            spider_name: 爬虫脚本名称
            database: 数据库，保存程序采集记录保存的数据库
            crawl_time: 采集时间，程序运行时间

        Returns:
            None
        """
        sql = f"""
        select concat(
        'select "', TABLE_NAME, '", count(id) as num , crawl_time from ', TABLE_SCHEMA, '.', TABLE_NAME,
        ' where crawl_time = "{crawl_time}"') from information_schema.tables
        where TABLE_SCHEMA='{database}' and TABLE_NAME in
        (SELECT TABLE_NAME FROM information_schema.columns WHERE COLUMN_NAME='crawl_time');
        """
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

    def insert_table_statistics(
        self, data: dict, table: str = "table_collection_statistics"
    ):
        """
        插入统计数据到表中
        Args:
            data: 需要统计的入库信息
            table: 存储表的名称

        Returns:
            None
        """
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table}` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `database` varchar(255) NOT NULL DEFAULT '-' COMMENT '采集程序和记录信息存储的数据库名',
            `spider_name` varchar(255) NOT NULL DEFAULT '-' COMMENT '脚本名称',
            `crawl_time` datetime NOT NULL COMMENT '程序运行/数据采集时间',
            `table_name` varchar(255) NOT NULL COMMENT '此项目所在库（一般某个项目放在单独的数据库中）的当前表名',
            `number` varchar(255) NOT NULL COMMENT '当前表的当前 crawl_time 的采集个数',
            PRIMARY KEY (`id`) USING BTREE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC COMMENT='项目对应库中各表采集统计表';
        """
        self.cursor.execute(create_table_sql)

        sql = self._get_sql_by_item(table=table, item=data)
        self._log_record(sql=sql, data=tuple(data.values()) * 2)

    @retry(
        stop_max_attempt_number=Param.retry_num,
        wait_random_min=Param.retry_time_min,
        wait_random_max=Param.retry_time_max,
    )
    def insert_script_statistics(
        self, data: dict, table: str = "script_collection_statistics"
    ):
        """
        存储运行脚本的统计信息
        Args:
            data: 需要插入的 log 信息
            table: 存储表的名称

        Returns:
            None
        """
        self.cursor.execute(
            f"""
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
            """
        )

        sql = self._get_sql_by_item(table=table, item=data)
        self._log_record(sql=sql, data=tuple(data.values()) * 2)

    def _log_record(self, sql: str, data: Tuple) -> None:
        """
        执行日志记录的 sql 语句
        Args:
            sql: sql 语句
            data: sql 语句中的参数

        Returns:
            None
        """
        try:
            if self.cursor.execute(sql, data):
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.slog.warning(f":{e}")
