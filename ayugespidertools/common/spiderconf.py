from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

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
)
from ayugespidertools.common.utils import Tools

__all__ = [
    "ESConfCreator",
    "KafkaConfCreator",
    "MQConfCreator",
    "MongoDBConfCreator",
    "MysqlConfCreator",
    "OracleConfCreator",
    "OssConfCreator",
    "PostgreSQLConfCreator",
    "ProxyCreator",
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
    ProxyConf,
    PostgreSQLConf,
    ESConf,
    OracleConf,
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


class Creator(ABC, Generic[SpiderConf]):
    @abstractmethod
    def create_product(self) -> Product[SpiderConf]:
        raise NotImplementedError(
            "Subclasses must implement the 'create_product' method"
        )


class MysqlConfProduct(Product[MysqlConf]):
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


class MongoDBConfProduct(Product[MongoDBConf]):
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


class PostgreSQLConfProduct(Product[PostgreSQLConf]):
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


class ESConfProduct(Product[ESConf]):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> ESConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(
                conf_name="elasticsearch", **remote_option
            )
            return ESConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("ES_CONFIG")
        return ESConf(**local_conf) if local_conf else None


class OracleConfProduct(Product[OracleConf]):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> OracleConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="oracle", **remote_option)
            return OracleConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("ORACLE_CONFIG")
        return OracleConf(**local_conf) if local_conf else None


class MQConfProduct(Product[MQConf]):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> MQConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="rabbitmq", **remote_option)
            return MQConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("MQ_CONFIG")
        return MQConf(**local_conf) if local_conf else None


class KafkaConfProduct(Product[KafkaConf]):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> KafkaConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="kafka", **remote_option)
            return KafkaConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("KAFKA_CONFIG")
        return KafkaConf(**local_conf) if local_conf else None


class ProxyProduct(Product[ProxyConf]):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> ProxyConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="proxy", **remote_option)
            return ProxyConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("PROXY_CONFIG")
        return ProxyConf(**local_conf) if local_conf else None


class OssConfProduct(Product[OssConf]):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> OssConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="oss:ali", **remote_option)
            return OssConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("OSS_CONFIG")
        return OssConf(**local_conf) if local_conf else None


class MysqlConfCreator(Creator[MysqlConf]):
    def create_product(self) -> Product[MysqlConf]:
        return MysqlConfProduct()


class MongoDBConfCreator(Creator[MongoDBConf]):
    def create_product(self) -> Product[MongoDBConf]:
        return MongoDBConfProduct()


class PostgreSQLConfCreator(Creator[PostgreSQLConf]):
    def create_product(self) -> Product[PostgreSQLConf]:
        return PostgreSQLConfProduct()


class ESConfCreator(Creator[ESConf]):
    def create_product(self) -> Product[ESConf]:
        return ESConfProduct()


class OracleConfCreator(Creator[OracleConf]):
    def create_product(self) -> Product[OracleConf]:
        return OracleConfProduct()


class MQConfCreator(Creator[MQConf]):
    def create_product(self) -> Product[MQConf]:
        return MQConfProduct()


class KafkaConfCreator(Creator[KafkaConf]):
    def create_product(self) -> Product[KafkaConf]:
        return KafkaConfProduct()


class ProxyCreator(Creator[ProxyConf]):
    def create_product(self) -> Product[ProxyConf]:
        return ProxyProduct()


class OssConfCreator(Creator[OssConf]):
    def create_product(self) -> Product[OssConf]:
        return OssConfProduct()


def get_spider_conf(
    creator: Creator[SpiderConf], settings: Settings, remote_option: dict
) -> SpiderConf | None:
    product = creator.create_product()
    return product.get_conn_conf(settings, remote_option)
