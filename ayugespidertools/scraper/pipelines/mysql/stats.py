import dataclasses
import datetime

from ayugespidertools.common.Expend import MysqlErrorHandlingMixin
from ayugespidertools.common.Utils import ToolsForAyu

__all__ = ["AyuStatisticsMysqlPipeline"]


class AyuStatisticsMysqlPipeline(MysqlErrorHandlingMixin):
    """
    Mysql 存储且记录脚本运行状态的简单示例
    """

    # TODO: 此方法暂用于测试
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
        return cls(env=crawler.settings.get("ENV", ""))

    def open_spider(self, spider):
        self.slog = spider.slog
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(
            mysql_config=self.mysql_config
        )

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
        update = ",".join([f" `{key}` = %s" for key in data])
        sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"
        try:
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
