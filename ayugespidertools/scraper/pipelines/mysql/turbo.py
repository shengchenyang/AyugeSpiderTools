from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pymysql
from dbutils.pooled_db import PooledDB

from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = [
    "AyuTurboMysqlPipeline",
]

if TYPE_CHECKING:
    from pymysql.connections import Connection
    from pymysql.cursors import Cursor
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.common.typevars import MysqlConf, slogT
    from ayugespidertools.spiders import AyuSpider


class AyuTurboMysqlPipeline(AyuMysqlPipeline):
    mysql_conf: MysqlConf
    conn: Connection
    slog: slogT
    cursor: Cursor
    pool_db_conf: dict
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        self.pool_db_conf = self.crawler.settings.get("POOL_DB_CONFIG", None)
        self.slog = spider.slog
        if not self.pool_db_conf:
            spider.slog.warning("未配置 POOL_DB_CONFIG 参数，将使用其默认参数")
            self.pool_db_conf = {
                "maxconnections": 5,
                "maxcached": 0,
                "maxusage": 0,
                "blocking": True,
            }
        self.mysql_conf = spider.mysql_conf
        self._connect(spider.mysql_conf).close()

        # 添加 PooledDB 的配置
        self.conn = PooledDB(
            creator=pymysql,
            user=self.mysql_conf.user,
            password=self.mysql_conf.password,
            host=self.mysql_conf.host,
            port=self.mysql_conf.port,
            database=self.mysql_conf.database,
            charset=self.mysql_conf.charset,
            **self.pool_db_conf,
        ).connection()
        self.cursor = self.conn.cursor()
