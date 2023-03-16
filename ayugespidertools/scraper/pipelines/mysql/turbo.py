import pymysql
from dbutils.pooled_db import PooledDB

from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = ["AyuTurboMysqlPipeline"]


class AyuTurboMysqlPipeline(AyuMysqlPipeline):
    """
    Mysql 存储场景的 scrapy pipeline 扩展，使用 dbutils.pooled_db 实现
    """

    def __init__(self, pool_db_config, *args, **kwargs):
        super(AyuTurboMysqlPipeline, self).__init__(*args, **kwargs)
        self.pool_db_config = pool_db_config

    @classmethod
    def from_crawler(cls, crawler):
        pool_db_config = crawler.settings.get("POOL_DB_CONFIG", None)
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
                "maxconnections": 5,
                # 连接池中空闲连接的最大数量。默认0，即无最大数量限制
                "maxcached": 0,
                # 连接的最大使用次数。默认0，即无使用次数限制
                "maxusage": 0,
                # 连接数达到最大时，新连接是否可阻塞。默认False，即达到最大连接数时，再取新连接将会报错
                "blocking": True,
            }
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(
            mysql_config=self.mysql_config
        )

        # 判断目标数据库是否连接正常。若连接目标数据库错误时，创建缺失的目标数据库。这个并不需要此连接对象，直接关闭即可
        self._connect(pymysql_dict_config=self.mysql_config).close()

        # 添加 PooledDB 的配置
        self.mysql_config.update(self.pool_db_config)
        self.conn = PooledDB(creator=pymysql, **self.mysql_config).connection()
        self.cursor = self.conn.cursor()
