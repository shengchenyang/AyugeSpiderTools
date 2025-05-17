from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from retrying import retry

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin
from ayugespidertools.common.params import Param

__all__ = [
    "AyuStatisticsMysqlPipeline",
]

if TYPE_CHECKING:
    from pymysql.connections import Connection
    from pymysql.cursors import Cursor

    from ayugespidertools.common.typevars import MysqlConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuStatisticsMysqlPipeline(MysqlPipeEnhanceMixin):
    mysql_conf: MysqlConf
    conn: Connection
    slog: slogT
    cursor: Cursor
    crawl_time: datetime.date

    def open_spider(self, spider: AyuSpider) -> None:
        self.crawl_time = datetime.date.today()
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.conn = self._connect(self.mysql_conf)
        self.cursor = self.conn.cursor()

    def table_collection_statistics(
        self, spider_name: str, database: str, crawl_time: datetime.date
    ) -> None:
        """统计数据库入库数据，获取当前数据库中所有包含 crawl_time 字段的数据表的简要信息

        Args:
            spider_name: 爬虫脚本名称
            database: 数据库，保存程序采集记录保存的数据库
            crawl_time: 采集时间，程序运行时间
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
                    "crawl_time": str(row[2] or crawl_time),
                }
                self.insert_table_statistics(table_statistics)

    def insert_table_statistics(
        self, data: dict, table: str = "table_collection_statistics"
    ) -> None:
        """插入统计数据到表中

        Args:
            data: 需要统计的入库信息
            table: 存储表的名称
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

        sql, args = self._get_sql_by_item(
            table=table,
            item=data,
            odku_enable=self.mysql_conf.odku_enable,
        )
        self._log_record(sql=sql, data=args)

    @retry(
        stop_max_attempt_number=Param.retry_num,
        wait_random_min=Param.retry_time_min,
        wait_random_max=Param.retry_time_max,
    )
    def insert_script_statistics(
        self, data: dict, table: str = "script_collection_statistics"
    ) -> None:
        """存储运行脚本的统计信息

        Args:
            data: 需要插入的 log 信息
            table: 存储表的名称
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

        sql, args = self._get_sql_by_item(
            table=table,
            item=data,
            odku_enable=self.mysql_conf.odku_enable,
        )
        self._log_record(sql=sql, data=args)

    def _log_record(self, sql: str, data: tuple[Any]) -> None:
        """执行日志记录的 sql 语句

        Args:
            sql: sql 语句
            data: sql 语句中的参数
        """
        try:
            self.cursor.execute(sql, data)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.slog.warning(f"日志记录存储错误: {e}")

    def close_spider(self, spider: AyuSpider) -> None:
        log_info = self._get_log_by_spider(spider=spider, crawl_time=self.crawl_time)

        # 运行脚本统计信息
        self.insert_script_statistics(log_info)
        self.table_collection_statistics(
            spider_name=spider.name,
            database=spider.mysql_conf.database,
            crawl_time=self.crawl_time,
        )

        if self.conn:
            self.conn.close()

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        return item
