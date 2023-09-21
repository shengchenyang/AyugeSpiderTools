import threading
import time
from typing import TYPE_CHECKING, Any, Union

from scrapy.spiders import Spider
from sqlalchemy import create_engine

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.spiderconf import (
    DynamicProxyCreator,
    ExclusiveProxyCreator,
    KafkaConfCreator,
    MongoDBConfCreator,
    MQConfCreator,
    MysqlConfCreator,
    get_spider_conf,
)
from ayugespidertools.config import logger

__all__ = [
    "AyuSpider",
]

if TYPE_CHECKING:
    import logging

    from loguru import Logger
    from scrapy.crawler import Crawler
    from scrapy.http import Response
    from scrapy.settings import BaseSettings
    from typing_extensions import Self


class MySqlEngineClass:
    """mysql 链接句柄单例模式"""

    _instance_lock = threading.Lock()

    def __init__(self, engine_url):
        self.engine = create_engine(
            engine_url, pool_pre_ping=True, pool_recycle=3600 * 7
        )

    def __new__(cls, *args, **kwargs):
        if not hasattr(MySqlEngineClass, "_instance"):
            with cls._instance_lock:
                if not hasattr(MySqlEngineClass, "_instance"):
                    MySqlEngineClass._instance = object.__new__(cls)

        return MySqlEngineClass._instance


class AyuSpider(Spider):
    """用于初始配置 scrapy 的各种 setting 的值及 spider 全局变量等"""

    custom_common_settings = {
        "ROBOTSTXT_OBEY": False,
        "TELNETCONSOLE_ENABLED": False,
        "RETRY_TIMES": 3,
        "DEPTH_PRIORITY": -1,
        "ENV": "dev",
    }

    custom_debug_settings = {
        "LOG_LEVEL": "DEBUG",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 20,
        "RETRY_TIMES": 3,
        "REDIRECT_ENABLED": False,
        "DEPTH_PRIORITY": -1,
        "ENV": "test",
        # 数据库表枚举
        "DATA_ENUM": None,
        # 是否记录程序的采集情况基本信息到 Mysql 数据库
        "RECORD_LOG_TO_MYSQL": False,
    }

    custom_product_settings = {
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 20,
        "RETRY_TIMES": 3,
        "REDIRECT_ENABLED": False,
        "DEPTH_PRIORITY": -1,
        "ENV": "prod",
        "DATA_ENUM": None,
        "RECORD_LOG_TO_MYSQL": False,
    }

    SPIDER_TIME = time.strftime("%Y-%m-%d", time.localtime())
    # 是否启用 Debug 参数，默认激活 custom_common_settings
    settings_type = "common"
    project_content = ""
    custom_table_enum = None
    mysql_engine_enabled = False

    def parse(self, response: "Response", **kwargs: Any) -> Any:
        """实现所继承类的 abstract 方法 parse"""
        super(AyuSpider, self).parse(response, **kwargs)

    def __init__(self, *args: Any, **kwargs: Any):
        super(AyuSpider, self).__init__(*args, **kwargs)
        self.mysql_engine = None

    @property
    def slog(self) -> Union["Logger", "logging.LoggerAdapter"]:
        """本库的日志管理模块，使用 loguru 来管理日志
        注意：
            1. 本库不是通过适配器模式或 mixin 等方法对 scrapy logger 重写或扩展，而是
        新增一个 slog 的日志管理方法，目前感觉这样最适合；
            2. 本配置可与 Scrapy 的 spider.log 同时管理，根据场景可以自行配置。
        """
        loguru_conf_tmp = self.crawler.settings.get("LOGURU_CONFIG")
        loguru_enabled = self.crawler.settings.get("LOGURU_ENABLED", True)
        assert isinstance(loguru_enabled, bool), "loguru_enabled 参数格式需要为 bool"

        if loguru_enabled:
            # 使用 LOGURU_CONFIG 下的配置，或直接使用统一管理的 logger
            return loguru_conf_tmp or logger

        # 如果关闭推荐的日志管理，则替换为 scrapy 的日志管理
        else:
            return super(AyuSpider, self).logger

    @classmethod
    def update_settings(cls, settings: "BaseSettings") -> None:
        custom_table_enum = getattr(cls, "custom_table_enum", None)
        # 设置类型，用于快速设置某些场景下的通用配置。比如测试 test 和生产 prod 下的通用配置；可不设置，默认为 common
        settings_type = getattr(cls, "settings_type", "common")
        inner_settings = getattr(cls, f"custom_{settings_type}_settings", {})

        if custom_table_enum:
            inner_settings["DATA_ENUM"] = custom_table_enum

        if vit_dir := settings.get("VIT_DIR", None):
            # 根据 vit_dir 配置，获取对应的 inner_settings 配置
            inner_settings = ReuseOperation.get_conf_by_settings(
                vit_dir=vit_dir, inner_settings=inner_settings
            )

        else:
            logger.warning("请在 settings.py 中配置 VIT_DIR 的路径参数，用于本库运行所需配置 .conf 的读取！")
        # 内置配置 inner_settings 优先级介于 project 和 spider 之间
        # 即优先级顺序：project_settings < inner_settings < custom_settings
        settings.setdict(inner_settings, priority="project")
        settings.setdict(cls.custom_settings or {}, priority="spider")

    @classmethod
    def from_crawler(cls, crawler: "Crawler", *args: Any, **kwargs: Any) -> "Self":
        spider = super(AyuSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.slog.debug(f"settings_type 配置: {cls.settings_type}")

        _consul_conf = ReuseOperation.get_consul_conf(settings=crawler.settings)
        # 以下将 .conf 中或 consul 中对应的配置信息，赋值给 spider 对象，方便后续使用
        if mysql_conf := get_spider_conf(
            MysqlConfCreator().create_product(crawler.settings, _consul_conf)
        ):
            spider.mysql_conf = mysql_conf
            if cls.mysql_engine_enabled:
                mysql_url = (
                    f"mysql+pymysql://{mysql_conf.user}"
                    f":{mysql_conf.password}@{mysql_conf.host}"
                    f":{mysql_conf.port}/{mysql_conf.database}"
                    f"?charset={mysql_conf.charset}"
                )
                spider.mysql_engine = MySqlEngineClass(engine_url=mysql_url).engine

        if mongodb_conf := get_spider_conf(
            MongoDBConfCreator().create_product(crawler.settings, _consul_conf)
        ):
            spider.mongodb_conf = mongodb_conf

        if rabbitmq_conf := get_spider_conf(
            MQConfCreator().create_product(crawler.settings, _consul_conf)
        ):
            spider.rabbitmq_conf = rabbitmq_conf

        if kafka_conf := get_spider_conf(
            KafkaConfCreator().create_product(crawler.settings, _consul_conf)
        ):
            spider.kafka_conf = kafka_conf

        if dynamicproxy_conf := get_spider_conf(
            DynamicProxyCreator().create_product(crawler.settings, _consul_conf)
        ):
            spider.dynamicproxy_conf = dynamicproxy_conf

        if exclusiveproxy_conf := get_spider_conf(
            ExclusiveProxyCreator().create_product(crawler.settings, _consul_conf)
        ):
            spider.exclusiveproxy_conf = exclusiveproxy_conf
        return spider
