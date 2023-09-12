from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, TypeVar

from ayugespidertools.common.typevars import (
    DynamicProxyConf,
    ExclusiveProxyConf,
    KafkaConf,
    MongoDBConf,
    MQConf,
    MysqlConf,
)
from ayugespidertools.common.utils import ToolsForAyu

__all__ = [
    "get_spider_conf",
    "MysqlConfCreator",
    "MongoDBConfCreator",
    "MQConfCreator",
    "KafkaConfCreator",
    "DynamicProxyCreator",
    "ExclusiveProxyCreator",
]

if TYPE_CHECKING:
    from scrapy.settings import Settings

SpiderConf = TypeVar(
    "SpiderConf",
    MysqlConf,
    MongoDBConf,
    MQConf,
    KafkaConf,
    DynamicProxyConf,
    ExclusiveProxyConf,
)


class Product(ABC):
    @abstractmethod
    def get_conn_conf(self):
        """获取各个工具链接配置信息"""
        pass


class Creator(ABC):
    @abstractmethod
    def create_product(self, *args, **kwargs) -> Product:
        pass


class MysqlConfProduct(Product):
    def __init__(self, settings: "Settings", consul_conf: dict):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_conn_conf(self):
        # 1). 优先从 consul 中取值
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            consul_conf = ToolsForAyu.get_conf_by_consul(
                conf_name="mysql", **self._consul_conf
            )
            return MysqlConf(**consul_conf) if consul_conf else None

        # 2). 从本地参数中取值
        local_conf = self._settings.get("MYSQL_CONFIG")
        return MysqlConf(**local_conf) if local_conf else None


class MongoDBConfProduct(Product):
    def __init__(self, settings, consul_conf):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            consul_conf = ToolsForAyu.get_conf_by_consul(
                conf_name="mongodb", **self._consul_conf
            )
            return MongoDBConf(**consul_conf) if consul_conf else None

        local_conf = self._settings.get("MONGODB_CONFIG")
        return MongoDBConf(**local_conf) if local_conf else None


class MQConfProduct(Product):
    def __init__(self, settings, consul_conf):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            consul_conf = ToolsForAyu.get_conf_by_consul(
                conf_name="rabbitmq", **self._consul_conf
            )
            return MQConf(**consul_conf) if consul_conf else None

        local_conf = self._settings.get("MQ_CONFIG")
        return MQConf(**local_conf) if local_conf else None


class KafkaConfProduct(Product):
    def __init__(self, settings, consul_conf):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            consul_conf = ToolsForAyu.get_conf_by_consul(
                conf_name="kafka", **self._consul_conf
            )
            return KafkaConf(**consul_conf) if consul_conf else None

        local_conf = self._settings.get("KAFKA_CONFIG")
        return KafkaConf(**local_conf) if local_conf else None


class DynamicProxyProduct(Product):
    def __init__(self, settings, consul_conf):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            consul_conf = ToolsForAyu.get_conf_by_consul(
                conf_name="dynamicproxy", **self._consul_conf
            )
            return DynamicProxyConf(**consul_conf) if consul_conf else None

        local_conf = self._settings.get("DYNAMIC_PROXY_CONFIG")
        return DynamicProxyConf(**local_conf) if local_conf else None


class ExclusiveProxyProduct(Product):
    def __init__(self, settings, consul_conf):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            consul_conf = ToolsForAyu.get_conf_by_consul(
                conf_name="exclusiveproxy", **self._consul_conf
            )
            return ExclusiveProxyConf(**consul_conf) if consul_conf else None

        local_conf = self._settings.get("EXCLUSIVE_PROXY_CONFIG")
        return ExclusiveProxyConf(**local_conf) if local_conf else None


class MysqlConfCreator(Creator):
    def create_product(self, settings: "Settings", consul_conf: dict) -> Product:
        return MysqlConfProduct(settings, consul_conf)


class MongoDBConfCreator(Creator):
    def create_product(self, settings: "Settings", consul_conf: dict) -> Product:
        return MongoDBConfProduct(settings, consul_conf)


class MQConfCreator(Creator):
    def create_product(self, settings: "Settings", consul_conf: dict) -> Product:
        return MQConfProduct(settings, consul_conf)


class KafkaConfCreator(Creator):
    def create_product(self, settings: "Settings", consul_conf: dict) -> Product:
        return KafkaConfProduct(settings, consul_conf)


class DynamicProxyCreator(Creator):
    def create_product(self, settings: "Settings", consul_conf: dict) -> Product:
        return DynamicProxyProduct(settings, consul_conf)


class ExclusiveProxyCreator(Creator):
    def create_product(self, settings: "Settings", consul_conf: dict) -> Product:
        return ExclusiveProxyProduct(settings, consul_conf)


def get_spider_conf(
    product: Product,
) -> Optional[SpiderConf]:
    return product.get_conn_conf()
