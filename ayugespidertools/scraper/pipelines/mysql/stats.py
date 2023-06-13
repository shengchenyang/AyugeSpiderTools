import dataclasses
import datetime

from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.scraper.pipelines import AyuMysqlPipeline

__all__ = [
    "AyuStatisticsMysqlPipeline",
]


class AyuStatisticsMysqlPipeline(AyuMysqlPipeline):
    """
    Mysql 存储且记录脚本运行状态的简单示例
    """

    # Note: 此方法暂用于测试
    def __init__(self, env):
        self.env = env
        self.slog = None
        self.conn = None
        self.cursor = None
        self.collate = None
        self.mysql_conf = None
        self.crawl_time = datetime.date.today()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(env=crawler.settings.get("ENV", ""))

    def open_spider(self, spider):
        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=self.mysql_conf)

        self.conn = self._connect(self.mysql_conf)
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
        sql = self._get_sql_by_item(table=table, item=data)
        self._log_record(sql=sql, data=tuple(data.values()) * 2)

    def close_spider(self, spider):
        log_info = self._get_log_by_spider(spider=spider, crawl_time=self.crawl_time)
        self.insert(log_info, "script_collection_statistics")

        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        return item
