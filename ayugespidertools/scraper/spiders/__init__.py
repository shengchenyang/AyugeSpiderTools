import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from scrapy.spiders import Spider

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.spiderconf import (
    DynamicProxyCreator,
    ExclusiveProxyCreator,
    KafkaConfCreator,
    MongoDBConfCreator,
    MQConfCreator,
    MysqlConfCreator,
    PostgreSQLConfCreator,
    get_spider_conf,
)
from ayugespidertools.common.typevars import DatabaseEngineClass
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


class AyuSpider(Spider):
    """用于初始配置 scrapy 的各种 setting 的值及 spider 全局变量等"""

    SPIDER_TIME: str = time.strftime("%Y-%m-%d", time.localtime())

    def parse(self, response: "Response", **kwargs: Any) -> Any:
        """实现所继承类的 abstract 方法 parse"""
        super(AyuSpider, self).parse(response, **kwargs)

    def __init__(self, *args: Any, **kwargs: Any):
        super(AyuSpider, self).__init__(*args, **kwargs)
        self.mysql_engine = None
        self.postgres_engine = None

    @property
    def slog(self) -> Union["Logger", "logging.LoggerAdapter"]:
        """本库的日志管理模块，使用 loguru 来管理日志
        注意：
            1. 本库不是通过适配器模式或 mixin 等方法对 scrapy logger 重写或扩展，而是
        新增一个 slog 的日志管理方法，目前感觉这样最适合；
            2. 本配置可与 Scrapy 的 spider.log 同时管理，根据场景可以自行配置。
        """
        loguru_enabled = self.crawler.settings.get("LOGURU_ENABLED", True)
        assert isinstance(loguru_enabled, bool), "loguru_enabled 参数格式需要为 bool"

        if loguru_enabled:
            return logger
        else:
            return super(AyuSpider, self).logger

    @classmethod
    def update_settings(cls, settings: "BaseSettings") -> None:
        _normal_settings = {
            "ROBOTSTXT_OBEY": False,
            "TELNETCONSOLE_ENABLED": False,
            "DEPTH_PRIORITY": -1,
        }

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
            _normal_settings["VIT_DIR"] = vit_dir

        # 根据本地配置获取对应的 inner_settings
        inner_settings = ReuseOperation.fetch_local_conf(
            vit_dir=vit_dir, inner_settings=_normal_settings
        )
        settings.setdict(inner_settings, priority="project")
        settings.setdict(cls.custom_settings or {}, priority="spider")

    @classmethod
    def from_crawler(cls, crawler: "Crawler", *args: Any, **kwargs: Any) -> "Self":
        spider = super(AyuSpider, cls).from_crawler(crawler, *args, **kwargs)

        remote_option = ReuseOperation.get_remote_option(settings=crawler.settings)
        # 将本地 .conf 或远程（consul, nacos）中对应的配置信息，赋值给 spider 对象
        if mysql_conf := get_spider_conf(
            MysqlConfCreator(), crawler.settings, remote_option
        ):
            spider.mysql_conf = mysql_conf
            if crawler.settings.get("DATABASE_ENGINE_ENABLED", False):
                mysql_url = (
                    f"mysql+pymysql://{mysql_conf.user}"
                    f":{mysql_conf.password}@{mysql_conf.host}"
                    f":{mysql_conf.port}/{mysql_conf.database}"
                    f"?charset={mysql_conf.charset}"
                )
                spider.mysql_engine = DatabaseEngineClass(engine_url=mysql_url).engine

        if mongodb_conf := get_spider_conf(
            MongoDBConfCreator(), crawler.settings, remote_option
        ):
            spider.mongodb_conf = mongodb_conf

        if postgres_conf := get_spider_conf(
            PostgreSQLConfCreator(), crawler.settings, remote_option
        ):
            spider.postgres_conf = postgres_conf
            if crawler.settings.get("DATABASE_ENGINE_ENABLED", False):
                postgres_url = (
                    f"postgresql+psycopg://{postgres_conf.user}:{postgres_conf.password}"
                    f"@{postgres_conf.host}:{postgres_conf.port}/{postgres_conf.database}"
                )
                spider.postgres_engine = DatabaseEngineClass(
                    engine_url=postgres_url
                ).engine

        if rabbitmq_conf := get_spider_conf(
            MQConfCreator(), crawler.settings, remote_option
        ):
            spider.rabbitmq_conf = rabbitmq_conf

        if kafka_conf := get_spider_conf(
            KafkaConfCreator(), crawler.settings, remote_option
        ):
            spider.kafka_conf = kafka_conf

        if dynamicproxy_conf := get_spider_conf(
            DynamicProxyCreator(), crawler.settings, remote_option
        ):
            spider.dynamicproxy_conf = dynamicproxy_conf

        if exclusiveproxy_conf := get_spider_conf(
            ExclusiveProxyCreator(), crawler.settings, remote_option
        ):
            spider.exclusiveproxy_conf = exclusiveproxy_conf
        return spider
