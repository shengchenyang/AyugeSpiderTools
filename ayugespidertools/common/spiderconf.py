from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

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
)
from ayugespidertools.common.utils import Tools

__all__ = [
    "DynamicProxyCreator",
    "ESConfCreator",
    "ExclusiveProxyCreator",
    "KafkaConfCreator",
    "MQConfCreator",
    "MongoDBConfCreator",
    "MysqlConfCreator",
    "OracleConfCreator",
    "OssConfCreator",
    "PostgreSQLConfCreator",
    "get_spider_conf",
]

if TYPE_CHECKING:
    from scrapy.settings import Settings

SpiderConf = TypeVar(
    "SpiderConf",
    MysqlConf,
    MongoDBConf,
    MQConf,
    KafkaConf,
    OssConf,
    DynamicProxyConf,
    ExclusiveProxyConf,
)


class Product(ABC, Generic[SpiderConf]):
    @abstractmethod
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> SpiderConf | None:
        """获取各个工具链接配置信息"""
        raise NotImplementedError(
            "Subclasses must implement the 'get_conn_conf' method"
        )


class Creator(ABC):
    @abstractmethod
    def create_product(self) -> Product:
        raise NotImplementedError(
            "Subclasses must implement the 'create_product' method"
        )


class MysqlConfProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> MysqlConf | None:
        # 1). 优先从远程配置中取值
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="mysql", **remote_option)
            return MysqlConf(**remote_conf) if remote_conf else None

        # 2). 从本地参数中取值
        local_conf = settings.get("MYSQL_CONFIG")
        return MysqlConf(**local_conf) if local_conf else None


class MongoDBConfProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> MongoDBConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            uri_remote_conf = Tools.fetch_remote_conf(
                conf_name="mongodb:uri", **remote_option
            )
            normal_remote_conf = Tools.fetch_remote_conf(
                conf_name="mongodb", **remote_option
            )
            remote_conf = uri_remote_conf or normal_remote_conf
            return MongoDBConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("MONGODB_CONFIG")
        return MongoDBConf(**local_conf) if local_conf else None


class PostgreSQLConfProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> PostgreSQLConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(
                conf_name="postgresql", **remote_option
            )
            return PostgreSQLConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("POSTGRESQL_CONFIG")
        return PostgreSQLConf(**local_conf) if local_conf else None


class ESConfProduct(Product):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> ESConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(
                conf_name="elasticsearch", **remote_option
            )
            return ESConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("ES_CONFIG")
        return ESConf(**local_conf) if local_conf else None


class OracleConfProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> OracleConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="oracle", **remote_option)
            return OracleConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("ORACLE_CONFIG")
        return OracleConf(**local_conf) if local_conf else None


class MQConfProduct(Product):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> MQConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="rabbitmq", **remote_option)
            return MQConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("MQ_CONFIG")
        return MQConf(**local_conf) if local_conf else None


class KafkaConfProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> KafkaConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="kafka", **remote_option)
            return KafkaConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("KAFKA_CONFIG")
        return KafkaConf(**local_conf) if local_conf else None


class DynamicProxyProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> DynamicProxyConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(
                conf_name="dynamicproxy", **remote_option
            )
            return DynamicProxyConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("DYNAMIC_PROXY_CONFIG")
        return DynamicProxyConf(**local_conf) if local_conf else None


class ExclusiveProxyProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> ExclusiveProxyConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(
                conf_name="exclusiveproxy", **remote_option
            )
            return ExclusiveProxyConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("EXCLUSIVE_PROXY_CONFIG")
        return ExclusiveProxyConf(**local_conf) if local_conf else None


class OssConfProduct(Product):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> OssConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="oss:ali", **remote_option)
            return OssConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("OSS_CONFIG")
        return OssConf(**local_conf) if local_conf else None


class MysqlConfCreator(Creator):
    def create_product(self) -> Product:
        return MysqlConfProduct()


class MongoDBConfCreator(Creator):
    def create_product(self) -> Product:
        return MongoDBConfProduct()


class PostgreSQLConfCreator(Creator):
    def create_product(self) -> Product:
        return PostgreSQLConfProduct()


class ESConfCreator(Creator):
    def create_product(self) -> Product:
        return ESConfProduct()


class OracleConfCreator(Creator):
    def create_product(self) -> Product:
        return OracleConfProduct()


class MQConfCreator(Creator):
    def create_product(self) -> Product:
        return MQConfProduct()


class KafkaConfCreator(Creator):
    def create_product(self) -> Product:
        return KafkaConfProduct()


class DynamicProxyCreator(Creator):
    def create_product(self) -> Product:
        return DynamicProxyProduct()


class ExclusiveProxyCreator(Creator):
    def create_product(self) -> Product:
        return ExclusiveProxyProduct()


class OssConfCreator(Creator):
    def create_product(self) -> Product:
        return OssConfProduct()


def get_spider_conf(
    creator: Creator, settings: Settings, remote_option: dict
) -> SpiderConf | None:
    product = creator.create_product()
    return product.get_conn_conf(settings, remote_option)
