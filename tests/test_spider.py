import inspect
import unittest
import warnings
from unittest import mock

import loguru
from scrapy import signals
from scrapy.settings import Settings
from scrapy.spiders import Spider
from scrapy.utils.test import get_crawler

from ayugespidertools.scraper.spiders import AyuSpider
from tests import CONSUL_CONFIG, MONGODB_CONFIG, MYSQL_CONFIG, tests_vitdir
from tests.conftest import ForTestConfig


class SpiderTest(unittest.TestCase):
    spider_class = AyuSpider
    scrapy_spider_class = Spider

    def setUp(self):
        warnings.simplefilter("always")

    def tearDown(self):
        warnings.resetwarnings()

    def test_base_spider(self):
        spider = self.spider_class("example.com")
        assert spider.name == "example.com"
        assert spider.start_urls == []

    def test_start_requests(self):
        spider = self.spider_class("example.com")
        start_requests = spider.start_requests()
        self.assertTrue(inspect.isgenerator(start_requests))
        self.assertEqual(list(start_requests), [])

    def test_spider_args(self):
        """``__init__`` method arguments are assigned to spider attributes"""
        spider = self.spider_class("example.com", foo="bar")
        self.assertEqual(spider.foo, "bar")

    def test_spider_without_name(self):
        """``__init__`` method arguments are assigned to spider attributes"""
        self.assertRaises(ValueError, self.spider_class)
        self.assertRaises(ValueError, self.spider_class, somearg="foo")

    def test_from_crawler_crawler_and_settings_population(self):
        crawler = get_crawler()
        spider = self.spider_class.from_crawler(crawler, "example.com")
        assert hasattr(spider, "crawler")
        assert spider.crawler is crawler
        assert hasattr(spider, "settings")
        assert spider.settings is crawler.settings

    def test_from_crawler_init_call(self):
        with mock.patch.object(
            self.spider_class, "__init__", return_value=None
        ) as mock_init:
            self.spider_class.from_crawler(get_crawler(), "example.com", foo="bar")
            mock_init.assert_called_once_with("example.com", foo="bar")

    def test_closed_signal_call(self):
        class TestSpider(self.spider_class):
            closed_called = False

            def closed(self, reason):
                self.closed_called = True

        crawler = get_crawler()
        spider = TestSpider.from_crawler(crawler, "example.com")
        crawler.signals.send_catch_log(signal=signals.spider_opened, spider=spider)
        crawler.signals.send_catch_log(
            signal=signals.spider_closed, spider=spider, reason=None
        )
        assert spider.closed_called

    def test_update_settings(self):
        spider_settings = {"TEST1": "spider", "TEST2": "spider"}
        project_settings = {
            "TEST1": "project",
            "TEST3": "project",
            "VIT_DIR": tests_vitdir,
        }
        self.spider_class.custom_settings = spider_settings
        settings = Settings(project_settings, priority="project")

        self.spider_class.update_settings(settings)
        assert settings.get("TEST1") == "spider"
        assert settings.get("TEST2") == "spider"
        assert settings.get("TEST3") == "project"

    def test_slog(self):
        """测试 slog 的日志功能"""
        slog_info = "this is a test log."
        # 创建一个 sink 对象来捕获日志消息
        sink = []
        # 配置 loguru 日志记录器
        loguru.logger.remove()
        loguru.logger.add(
            lambda message: sink.append(message), format="{message}", level="INFO"
        )

        crawler = get_crawler()
        spider = self.spider_class.from_crawler(crawler, "example.com")
        spider.slog.info(slog_info)

        # 获取捕获的日志消息
        record = sink[0]
        assert str(record).strip() == slog_info

    def test_from_crawler_get_mysql_conf(self):
        """测试从爬虫 AyugeSpider(即 spider) 中获取 mysql 配置的方法"""
        # 测试本地 mysql 配置
        spider_settings = {"APP_CONF_MANAGE": False}
        spider_settings.update(ForTestConfig.scrapy_default_settings)
        project_settings = {"MYSQL_CONFIG": MYSQL_CONFIG, "VIT_DIR": tests_vitdir}
        self.spider_class.custom_settings = spider_settings
        settings = Settings(project_settings, priority="project")
        self.spider_class.update_settings(settings)

        crawler = get_crawler(settings_dict=dict(settings))
        spider = self.spider_class.from_crawler(crawler, "example.com")
        assert hasattr(spider, "mysql_conf")
        assert spider.mysql_conf._asdict() == MYSQL_CONFIG

        # 测试应用管理中心 mysql 配置
        CONSUL_CONF = {
            "token": CONSUL_CONFIG["token"],
            "url": CONSUL_CONFIG["url"],
            "format": CONSUL_CONFIG["format"],
            "remote_type": "consul",
        }
        spider_settings = {"APP_CONF_MANAGE": True}
        spider_settings.update(ForTestConfig.scrapy_default_settings)
        project_settings = {"REMOTE_CONFIG": CONSUL_CONF, "VIT_DIR": tests_vitdir}
        self.spider_class.custom_settings = spider_settings
        settings = Settings(project_settings, priority="project")
        self.spider_class.update_settings(settings)

        crawler = get_crawler(settings_dict=dict(settings))
        spider = self.spider_class.from_crawler(crawler, "example.com")
        assert hasattr(spider, "mysql_conf")
        assert spider.mysql_conf._asdict() == MYSQL_CONFIG

    def test_from_crawler_get_mongodb_conf(self):
        """测试从爬虫 AyugeSpider(即 spider) 中获取 mongodb 配置的方法"""
        # 测试本地 mongodb 配置
        local_mongodb_conf = {
            "host": MONGODB_CONFIG["host"],
            "port": MONGODB_CONFIG["port"],
            "user": MONGODB_CONFIG["user"],
            "password": MONGODB_CONFIG["password"],
            "authsource": MONGODB_CONFIG["authsource"],
            "authMechanism": MONGODB_CONFIG["authMechanism"],
            "database": MONGODB_CONFIG["database"],
            "uri": MONGODB_CONFIG["uri"],
        }
        spider_settings = {"APP_CONF_MANAGE": False}
        spider_settings.update(ForTestConfig.scrapy_default_settings)
        project_settings = {
            "MONGODB_CONFIG": local_mongodb_conf,
            "VIT_DIR": tests_vitdir,
        }
        self.spider_class.custom_settings = spider_settings
        settings = Settings(project_settings, priority="project")
        self.spider_class.update_settings(settings)

        crawler = get_crawler(settings_dict=dict(settings))
        spider = self.spider_class.from_crawler(crawler, "example.com")
        assert hasattr(spider, "mongodb_conf")
        _spider_mongodb_conf = spider.mongodb_conf._asdict()
        if _spider_mongodb_conf.get("uri") is not None:
            assert _spider_mongodb_conf["uri"] == local_mongodb_conf["uri"]

        # 测试应用管理中心 mongodb 配置
        CONSUL_CONF = {
            "token": CONSUL_CONFIG["token"],
            "url": CONSUL_CONFIG["url"],
            "format": CONSUL_CONFIG["format"],
            "remote_type": "consul",
        }
        spider_settings = {"APP_CONF_MANAGE": True}
        spider_settings.update(ForTestConfig.scrapy_default_settings)
        project_settings = {"REMOTE_CONFIG": CONSUL_CONF, "VIT_DIR": tests_vitdir}
        self.spider_class.custom_settings = spider_settings
        settings = Settings(project_settings, priority="project")
        self.spider_class.update_settings(settings)

        crawler = get_crawler(settings_dict=dict(settings))
        spider = self.spider_class.from_crawler(crawler, "example.com")
        assert hasattr(spider, "mongodb_conf")
        _spider_mongodb_conf = spider.mongodb_conf._asdict()
        # 如果配置了 mongodb:uri 则优先获取 uri 配置
        if _spider_mongodb_conf.get("uri") is not None:
            assert _spider_mongodb_conf["uri"] == local_mongodb_conf["uri"]
        # 否则获取 MongoDBConf 除了 uri 的所有参数
        else:
            _spider_mongodb_conf.pop("uri", None)
            local_mongodb_conf.pop("uri", None)
            assert _spider_mongodb_conf == local_mongodb_conf
