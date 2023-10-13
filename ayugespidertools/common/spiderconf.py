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
    def __init__(self, settings: "Settings", remote_option: dict):
        self._settings = settings
        self._remote_option = remote_option

    def get_conn_conf(self):
        # 1). 优先从远程配置中取值
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="mysql", **self._remote_option
            )
            return MysqlConf(**remote_conf) if remote_conf else None

        # 2). 从本地参数中取值
        local_conf = self._settings.get("MYSQL_CONFIG")
        return MysqlConf(**local_conf) if local_conf else None


class MongoDBConfProduct(Product):
    def __init__(self, settings, remote_option):
        self._settings = settings
        self._remote_option = remote_option

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="mongodb", **self._remote_option
            )
            return MongoDBConf(**remote_conf) if remote_conf else None

        local_conf = self._settings.get("MONGODB_CONFIG")
        return MongoDBConf(**local_conf) if local_conf else None


class MQConfProduct(Product):
    def __init__(self, settings, remote_option):
        self._settings = settings
        self._remote_option = remote_option

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="rabbitmq", **self._remote_option
            )
            return MQConf(**remote_conf) if remote_conf else None

        local_conf = self._settings.get("MQ_CONFIG")
        return MQConf(**local_conf) if local_conf else None


class KafkaConfProduct(Product):
    def __init__(self, settings, remote_option):
        self._settings = settings
        self._remote_option = remote_option

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="kafka", **self._remote_option
            )
            return KafkaConf(**remote_conf) if remote_conf else None

        local_conf = self._settings.get("KAFKA_CONFIG")
        return KafkaConf(**local_conf) if local_conf else None


class DynamicProxyProduct(Product):
    def __init__(self, settings, remote_option):
        self._settings = settings
        self._remote_option = remote_option

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="dynamicproxy", **self._remote_option
            )
            return DynamicProxyConf(**remote_conf) if remote_conf else None

        local_conf = self._settings.get("DYNAMIC_PROXY_CONFIG")
        return DynamicProxyConf(**local_conf) if local_conf else None


class ExclusiveProxyProduct(Product):
    def __init__(self, settings, remote_option):
        self._settings = settings
        self._remote_option = remote_option

    def get_conn_conf(self):
        if _ := self._settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="exclusiveproxy", **self._remote_option
            )
            return ExclusiveProxyConf(**remote_conf) if remote_conf else None

        local_conf = self._settings.get("EXCLUSIVE_PROXY_CONFIG")
        return ExclusiveProxyConf(**local_conf) if local_conf else None


class MysqlConfCreator(Creator):
    def create_product(self, settings: "Settings", remote_option: dict) -> Product:
        return MysqlConfProduct(settings, remote_option)


class MongoDBConfCreator(Creator):
    def create_product(self, settings: "Settings", remote_option: dict) -> Product:
        return MongoDBConfProduct(settings, remote_option)


class MQConfCreator(Creator):
    def create_product(self, settings: "Settings", remote_option: dict) -> Product:
        return MQConfProduct(settings, remote_option)


class KafkaConfCreator(Creator):
    def create_product(self, settings: "Settings", remote_option: dict) -> Product:
        return KafkaConfProduct(settings, remote_option)


class DynamicProxyCreator(Creator):
    def create_product(self, settings: "Settings", remote_option: dict) -> Product:
        return DynamicProxyProduct(settings, remote_option)


class ExclusiveProxyCreator(Creator):
    def create_product(self, settings: "Settings", remote_option: dict) -> Product:
        return ExclusiveProxyProduct(settings, remote_option)


def get_spider_conf(
    product: Product,
) -> Optional[SpiderConf]:
    return product.get_conn_conf()
