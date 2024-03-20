from typing import TYPE_CHECKING

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

    from ayugespidertools.common.typevars import MysqlConf
    from ayugespidertools.spiders import AyuSpider


class AyuTurboMysqlPipeline(AyuMysqlPipeline):
    mysql_conf: "MysqlConf"
    conn: "Connection[Cursor]"
    cursor: "Cursor"
    pool_db_conf: dict

    def __init__(self, pool_db_conf: dict) -> None:
        self.pool_db_conf = pool_db_conf

    @classmethod
    def from_crawler(cls, crawler: "Crawler") -> "Self":
        pool_db_conf = crawler.settings.get("POOL_DB_CONFIG", None)
        return cls(
            pool_db_conf=pool_db_conf,
        )

    def open_spider(self, spider: "AyuSpider") -> None:
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"
        if not self.pool_db_conf:
            spider.slog.warning("未配置 POOL_DB_CONFIG 参数，将使用其默认参数")
            self.pool_db_conf = {
                "maxconnections": 5,
                # 连接池中空闲连接的最大数量。默认 0，即无最大数量限制
                "maxcached": 0,
                # 连接的最大使用次数。默认 0，即无使用次数限制
                "maxusage": 0,
                # 连接数达到最大时，新连接是否可阻塞。默认False，即达到最大连接数时，再取新连接将会报错
                "blocking": True,
            }
        self.mysql_conf = spider.mysql_conf

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。这个并不需要此连接对象，直接关闭即可
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
            **self.pool_db_conf
        ).connection()
        self.cursor = self.conn.cursor()
