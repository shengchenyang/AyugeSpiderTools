import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scrapy.spiders import Spider

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.spiderconf import (
    DynamicProxyCreator,
    ESConfCreator,
    ExclusiveProxyCreator,
    KafkaConfCreator,
    MongoDBConfCreator,
    MQConfCreator,
    MysqlConfCreator,
    OracleConfCreator,
    OssConfCreator,
    PostgreSQLConfCreator,
    get_spider_conf,
    get_sqlalchemy_conf,
)
from ayugespidertools.config import logger

__all__ = [
    "AyuSpider",
]

if TYPE_CHECKING:
    from elasticsearch import Elasticsearch
    from scrapy.crawler import Crawler
    from scrapy.settings import BaseSettings
    from sqlalchemy.engine.base import Connection as SqlalchemyConnectT
    from sqlalchemy.engine.base import Engine as SqlalchemyEngineT
    from typing_extensions import Self

    from ayugespidertools.common.typevars import (
        DynamicProxyConf,
        ESConf,
        ExclusiveProxyConf,
        KafkaConf,
        MongoDBConf,
        MQConf,
        MysqlConf,
        OracleConf,
        OssConf,
        PostgreSQLConf,
        slogT,
    )


class AyuSpider(Spider):
    mysql_engine: "SqlalchemyEngineT"
    mysql_engine_conn: "SqlalchemyConnectT"
    postgres_engine: "SqlalchemyEngineT"
    postgres_engine_conn: "SqlalchemyConnectT"
    oracle_engine: "SqlalchemyEngineT"
    oracle_engine_conn: "SqlalchemyConnectT"
    es_engine: "Elasticsearch"
    es_engine_conn: "Elasticsearch"

    mysql_conf: "MysqlConf"
    mongodb_conf: "MongoDBConf"
    postgres_conf: "PostgreSQLConf"
    es_conf: "ESConf"
    oracle_conf: "OracleConf"
    rabbitmq_conf: "MQConf"
    kafka_conf: "KafkaConf"
    dynamicproxy_conf: "DynamicProxyConf"
    exclusiveproxy_conf: "ExclusiveProxyConf"
    oss_conf: "OssConf"

    SPIDER_TIME: str = time.strftime("%Y-%m-%d", time.localtime())

    @property
    def slog(self) -> "slogT":
        """本库的日志管理模块，使用 loguru 来管理日志
        Note:
            本配置可与 Scrapy 的 spider.log 同时管理，根据场景可以自行配置。
        """
        loguru_enabled = self.crawler.settings.get("LOGURU_ENABLED", True)
        assert isinstance(loguru_enabled, bool), "loguru_enabled 参数格式需要为 bool"

        return logger if loguru_enabled else super(AyuSpider, self).logger

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

        inner_settings = ReuseOperation.fetch_local_conf(
            vit_dir=vit_dir, inner_settings=_normal_settings
        )
        settings.setdict(inner_settings, priority="project")
        settings.setdict(cls.custom_settings or {}, priority="spider")

    @classmethod
    def from_crawler(cls, crawler: "Crawler", *args: Any, **kwargs: Any) -> "Self":
        spider = super(AyuSpider, cls).from_crawler(crawler, *args, **kwargs)
        _db_engine_enabled = crawler.settings.get("DATABASE_ENGINE_ENABLED", False)

        remote_option = ReuseOperation.get_remote_option(settings=crawler.settings)
        # 将本地 .conf 或远程（consul, nacos）中对应的配置信息，赋值给 spider 对象
        if mysql_conf := get_spider_conf(
            MysqlConfCreator(), crawler.settings, remote_option
        ):
            spider.mysql_conf = mysql_conf
            spider.mysql_engine, spider.mysql_engine_conn = get_sqlalchemy_conf(
                creator=MysqlConfCreator(),
                db_conf=mysql_conf,
                db_engine_enabled=_db_engine_enabled,
            )

        if mongodb_conf := get_spider_conf(
            MongoDBConfCreator(), crawler.settings, remote_option
        ):
            spider.mongodb_conf = mongodb_conf

        if postgres_conf := get_spider_conf(
            PostgreSQLConfCreator(), crawler.settings, remote_option
        ):
            spider.postgres_conf = postgres_conf
            spider.postgres_engine, spider.postgres_engine_conn = get_sqlalchemy_conf(
                creator=PostgreSQLConfCreator(),
                db_conf=postgres_conf,
                db_engine_enabled=_db_engine_enabled,
            )

        if es_conf := get_spider_conf(ESConfCreator(), crawler.settings, remote_option):
            spider.es_conf = es_conf
            spider.es_engine = spider.es_engine_conn = get_sqlalchemy_conf(
                creator=ESConfCreator(),
                db_conf=es_conf,
                db_engine_enabled=_db_engine_enabled,
            )

        if oracle_conf := get_spider_conf(
            OracleConfCreator(), crawler.settings, remote_option
        ):
            spider.oracle_conf = oracle_conf
            spider.oracle_engine, spider.oracle_engine_conn = get_sqlalchemy_conf(
                creator=OracleConfCreator(),
                db_conf=oracle_conf,
                db_engine_enabled=_db_engine_enabled,
            )

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

        if oss_conf := get_spider_conf(
            OssConfCreator(), crawler.settings, remote_option
        ):
            spider.oss_conf = oss_conf
        return spider
