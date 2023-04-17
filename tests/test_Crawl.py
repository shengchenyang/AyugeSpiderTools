from scrapy import signals
from scrapy.spiders import Spider
from scrapy.utils.test import get_crawler
from testfixtures import LogCapture
from twisted.internet import defer
from twisted.trial.unittest import TestCase

from ayugespidertools.scraper.spiders import AyuSpider
from tests.conftest import script_coll_table, table_coll_table
from tests.mockserver import MockServer
from tests.spiders import DemoAiohttpSpider, MyAyuCrawlSpider, RecordLogToMysqlSpider


class TestCrawl(TestCase):
    spider_class = AyuSpider
    scrapy_spider_class = Spider

    def setUp(self):
        self.mockserver = MockServer()
        self.mockserver.__enter__()

    def tearDown(self):
        self.mockserver.__exit__(None, None, None)

    @defer.inlineCallbacks
    def _run_spider(self, spider_cls):
        items = []

        def _on_item_scraped(item):
            items.append(item)

        crawler = get_crawler(spider_cls)
        crawler.signals.connect(_on_item_scraped, signals.item_scraped)
        with LogCapture() as log:
            yield crawler.crawl(
                self.mockserver.url("/status?n=200"), mockserver=self.mockserver
            )
        return log, items, crawler.stats

    @defer.inlineCallbacks
    def test_from_crawler_record_log_to_mysql(self):
        """
        测试从爬虫 AyugeSpider(即 spider) 中记录日志到 mysql 的方法
        """
        log, _, stats = yield self._run_spider(RecordLogToMysqlSpider)
        # 此测试会经过 test_table_exists 检测目标数据表是否已存在
        self.assertIn("Got response 200", str(log))

    @defer.inlineCallbacks
    def test_My_AyuCrawlSpider(self):
        """
        测试 AyuCrawlSpider，对应 scrapy 的 CrawlSpider
        """
        log, _, stats = yield self._run_spider(MyAyuCrawlSpider)
        self.assertIn("book_name: ", str(log))

    @defer.inlineCallbacks
    def test_DemoAiohttpSpider(self):
        """
        测试 DemoAiohttpSpider 的 aiohttp 下载器功能
        """
        log, _, stats = yield self._run_spider(DemoAiohttpSpider)
        self.assertIn("get meta_data: ", str(log))
        self.assertIn("post first meta_data: ", str(log))
        self.assertIn("post second meta_data: ", str(log))


def test_table_exists(mysql_db_cursor):
    """
    检测目标数据表是否已存在，这是 test_from_crawler_record_log_to_mysql 测试的结果判断。
    用于查看脚本运行情况统计是否正常建表入库。
    """
    sql_front = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = "
    _script_coll_sql = f"{sql_front}'{script_coll_table}'"
    _table_coll_sql = f"{sql_front}'{table_coll_table}'"
    mysql_db_cursor.execute(_script_coll_sql)
    _select_res = mysql_db_cursor.fetchone()
    assert _select_res[0] == 1

    mysql_db_cursor.execute(_table_coll_sql)
    _select_res = mysql_db_cursor.fetchone()
    assert _select_res[0] == 1


def test_crawl():
    from ayugespidertools.commands.crawl import AyuCommand

    # 这部分不用测试，没有必要
    AyuCommand()
