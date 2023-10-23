import threading
import time
from pathlib import Path
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
        # 设置类型，用于快速设置某些通用配置，若不设置默认为 common
        settings_type = getattr(cls, "settings_type", "common")
        inner_settings = getattr(cls, f"custom_{settings_type}_settings", {})

        if custom_table_enum:
            inner_settings["DATA_ENUM"] = custom_table_enum

        if not (vit_dir := settings.get("VIT_DIR", None)):
            logger.warning("settings 中未配置 VIT_DIR，将从默认配置中获取！")
            exec_path = Path().resolve()
            _parts = exec_path.parts[-2:]
            assert len(_parts) >= 2, "执行脚本的路径可能存在问题！"
            vit_dir = (
                exec_path / "VIT"
                if _parts[0] == _parts[1]
                else exec_path / settings["BOT_NAME"] / "VIT"
            )

        # 根据本地配置获取对应的 inner_settings
        inner_settings = ReuseOperation.fetch_local_conf(
            vit_dir=vit_dir, inner_settings=inner_settings
        )
        settings.setdict(inner_settings, priority="project")
        settings.setdict(cls.custom_settings or {}, priority="spider")

    @classmethod
    def from_crawler(cls, crawler: "Crawler", *args: Any, **kwargs: Any) -> "Self":
        spider = super(AyuSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.slog.debug(f"settings_type 配置: {cls.settings_type}")

        remote_option = ReuseOperation.get_remote_option(settings=crawler.settings)
        # 将本地 .conf 或远程（consul, nacos）中对应的配置信息，赋值给 spider 对象
        if mysql_conf := get_spider_conf(
            MysqlConfCreator().create_product(crawler.settings, remote_option)
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
            MongoDBConfCreator().create_product(crawler.settings, remote_option)
        ):
            spider.mongodb_conf = mongodb_conf

        if rabbitmq_conf := get_spider_conf(
            MQConfCreator().create_product(crawler.settings, remote_option)
        ):
            spider.rabbitmq_conf = rabbitmq_conf

        if kafka_conf := get_spider_conf(
            KafkaConfCreator().create_product(crawler.settings, remote_option)
        ):
            spider.kafka_conf = kafka_conf

        if dynamicproxy_conf := get_spider_conf(
            DynamicProxyCreator().create_product(crawler.settings, remote_option)
        ):
            spider.dynamicproxy_conf = dynamicproxy_conf

        if exclusiveproxy_conf := get_spider_conf(
            ExclusiveProxyCreator().create_product(crawler.settings, remote_option)
        ):
            spider.exclusiveproxy_conf = exclusiveproxy_conf
        return spider
