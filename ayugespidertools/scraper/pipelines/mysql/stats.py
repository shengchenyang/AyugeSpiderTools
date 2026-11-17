from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, cast

from ayugespidertools.common.expend import MysqlPipeEnhanceMixin

__all__ = [
    "AyuStatisticsMysqlPipeline",
]

if TYPE_CHECKING:
    from typing import Self

    from pymysql.connections import Connection
    from pymysql.cursors import Cursor
    from scrapy.crawler import Crawler

    from ayugespidertools.common.typevars import MysqlConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuStatisticsMysqlPipeline(MysqlPipeEnhanceMixin):
    mysql_conf: MysqlConf
    conn: Connection
    slog: slogT
    cursor: Cursor
    crawl_time: datetime.date
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        self.crawl_time = datetime.date.today()
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.conn = self._connect(self.mysql_conf)
        self.cursor = self.conn.cursor()

    def table_collection_statistics(
        self, spider_name: str, database: str, crawl_time: datetime.date
    ) -> None:
        """Collect database insertion statistics for all tables containing a
        `crawl_time` column in the current database.

        Args:
            spider_name: The name of the spider script.
            database:  The database where the collection records are stored.
            crawl_time:  The program execution date.
        """
        sql = f"""
        select concat(
        'select "', TABLE_NAME, '", count(id) as num , crawl_time from ', TABLE_SCHEMA, '.', TABLE_NAME,
        ' where crawl_time = "{crawl_time}"') from information_schema.tables
        where TABLE_SCHEMA='{database}' and TABLE_NAME in
        (SELECT TABLE_NAME FROM information_schema.columns WHERE COLUMN_NAME='crawl_time');
        """  # noqa: S608
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
        """Insert collection statistics into a database table.

        Args:
            data: Table-level crawl statistics to insert.
            table: Destination statistics table name.
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

    def insert_script_statistics(
        self, data: dict, table: str = "script_collection_statistics"
    ) -> None:
        """Store spider-run statistics, creating the statistics table if needed.

        Args:
            data: Run statistics and diagnostic information to insert.
            table: Destination statistics table name.
        """
        script_statistics_sql = f"""
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
        self.cursor.execute(script_statistics_sql)

        sql, args = self._get_sql_by_item(
            table=table,
            item=data,
            odku_enable=self.mysql_conf.odku_enable,
        )
        self._log_record(sql=sql, data=args)

    def _log_record(self, sql: str, data: tuple[Any]) -> None:
        """Execute and commit a statistics INSERT statement.

        Roll back and log a warning if execution fails.

        Args:
            sql: SQL statement to execute.
            data: Parameter values to bind to the statement.
        """
        try:
            self.cursor.execute(sql, data)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.slog.warning(f"Failed to store crawl statistics: {e}")

    def close_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        log_info = self._get_log_by_spider(spider=spider, crawl_time=self.crawl_time)

        self.insert_script_statistics(log_info)
        self.table_collection_statistics(
            spider_name=spider.name,
            database=spider.mysql_conf.database,
            crawl_time=self.crawl_time,
        )

        if self.conn:
            self.conn.close()

    def process_item(self, item: Any) -> Any:
        return item
