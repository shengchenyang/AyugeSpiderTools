from __future__ import annotations

import importlib.util
import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from scrapy.spiders import Spider

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.spiderconf import (
    ESConfCreator,
    KafkaConfCreator,
    MongoDBConfCreator,
    MQConfCreator,
    MysqlConfCreator,
    OracleConfCreator,
    OssConfCreator,
    PostgreSQLConfCreator,
    ProxyCreator,
    get_spider_conf,
)
from ayugespidertools.config import logger
from ayugespidertools.exceptions import (
    AyugeSpiderToolsDeprecationWarning,
    NotConfigured,
)

__all__ = [
    "AyuSpider",
]

if TYPE_CHECKING:
    from typing import Self

    from scrapy.crawler import Crawler
    from scrapy.settings import BaseSettings

    from ayugespidertools.common.typevars import (
        ESConf,
        KafkaConf,
        MongoDBConf,
        MQConf,
        MysqlConf,
        OracleConf,
        OssConf,
        PostgreSQLConf,
        ProxyConf,
        slogT,
    )


class AyuSpider(Spider):
    mysql_conf: MysqlConf
    mongodb_conf: MongoDBConf
    postgres_conf: PostgreSQLConf
    es_conf: ESConf
    oracle_conf: OracleConf
    rabbitmq_conf: MQConf
    kafka_conf: KafkaConf
    proxy_conf: ProxyConf
    oss_conf: OssConf

    SPIDER_TIME: str = time.strftime("%Y-%m-%d", time.localtime())

    @property
    def slog(self) -> slogT:
        """Return the logger selected by the LOGURU_ENABLED setting.

        Use loguru when enabled; otherwise use Scrapy's Spider.logger.
        Scrapy's logger remains available independently of this property.
        """
        loguru_enabled = self.crawler.settings.get("LOGURU_ENABLED", True)
        assert isinstance(loguru_enabled, bool), "LOGURU_ENABLED must be a bool"

        return logger if loguru_enabled else super().logger

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        _normal_settings: dict[str, Any] = {
            "TELNETCONSOLE_ENABLED": False,
            "DEPTH_PRIORITY": -1,
        }

        if not (vit_dir := settings.get("VIT_DIR", None)):
            logger.warning(
                "VIT_DIR is not configured; deriving the default path from BOT_NAME!"
            )
            if module_spec := importlib.util.find_spec(settings["BOT_NAME"]):
                submodule_paths = module_spec.submodule_search_locations
                assert submodule_paths, "Project path is None or empty"
                assert len(submodule_paths) == 1, (
                    "The project package must have exactly one submodule search location;"
                    "please change your project name"
                )
                vit_dir = Path(*submodule_paths) / "VIT"
                _normal_settings["VIT_DIR"] = vit_dir
            else:
                raise NotConfigured("You must define the VIT_DIR parameter")

        inner_settings = ReuseOperation.fetch_local_conf(
            vit_dir=vit_dir, inner_settings=_normal_settings
        )
        settings.setdict(inner_settings, priority="project")
        settings.setdict(cls.custom_settings or {}, priority="spider")

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = cast("Self", super().from_crawler(crawler, *args, **kwargs))
        if crawler.settings.get("DATABASE_ENGINE_ENABLED") is not None:
            warnings.warn(
                "parameter 'DATABASE_ENGINE_ENABLED' is deprecated, use 'ayugespidertools.utils.database' instead",
                category=AyugeSpiderToolsDeprecationWarning,
                stacklevel=2,
            )

        remote_option = ReuseOperation.get_remote_option(settings=crawler.settings)
        # Attach connection settings from the local .conf file or remote Consul/Nacos configuration.
        if mysql_conf := get_spider_conf(
            MysqlConfCreator(), crawler.settings, remote_option
        ):
            spider.mysql_conf = mysql_conf

        if mongodb_conf := get_spider_conf(
            MongoDBConfCreator(), crawler.settings, remote_option
        ):
            spider.mongodb_conf = mongodb_conf

        if postgres_conf := get_spider_conf(
            PostgreSQLConfCreator(), crawler.settings, remote_option
        ):
            spider.postgres_conf = postgres_conf

        if es_conf := get_spider_conf(ESConfCreator(), crawler.settings, remote_option):
            spider.es_conf = es_conf

        if oracle_conf := get_spider_conf(
            OracleConfCreator(), crawler.settings, remote_option
        ):
            spider.oracle_conf = oracle_conf

        if rabbitmq_conf := get_spider_conf(
            MQConfCreator(), crawler.settings, remote_option
        ):
            spider.rabbitmq_conf = rabbitmq_conf

        if kafka_conf := get_spider_conf(
            KafkaConfCreator(), crawler.settings, remote_option
        ):
            spider.kafka_conf = kafka_conf

        if proxy_conf := get_spider_conf(
            ProxyCreator(), crawler.settings, remote_option
        ):
            spider.proxy_conf = proxy_conf

        if oss_conf := get_spider_conf(
            OssConfCreator(), crawler.settings, remote_option
        ):
            spider.oss_conf = oss_conf
        return spider
