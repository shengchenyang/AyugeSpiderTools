from abc import ABC, abstractmethod
from typing import Union

from scrapy.settings import Settings

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import MongoDBConf, MysqlConf
from ayugespidertools.common.utils import ToolsForAyu

__all__ = [
    "get_spider_db_conf",
    "MysqlConfCreator",
    "MongoDBConfCreator",
]


class Product(ABC):
    @abstractmethod
    def get_db_conn_conf(self) -> Union[MysqlConf, MongoDBConf, None]:
        """
        获取数据库链接配置信息，目前支持 mysql 和 mongodb
        """
        pass


class Creator(ABC):
    @abstractmethod
    def create_product(self, *args, **kwargs) -> Product:
        pass


class MysqlConfProduct(Product):
    def __init__(self, settings: Settings, consul_conf: dict):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_db_conn_conf(self) -> Union[MysqlConf, None]:
        # 自定义 mysql 链接配置
        local_mysql_conf = self._settings.get("LOCAL_MYSQL_CONFIG", {})
        # 是否开启应用配置管理
        app_conf_manage = self._settings.get("APP_CONF_MANAGE", False)
        if all([not local_mysql_conf.get("database"), not app_conf_manage]):
            return None

        # 1). 如果开启应用管理，从 consul 中获取应用配置
        if app_conf_manage:
            _consul_conf_dict = ToolsForAyu.get_conf_by_consul(
                conf_name="mysql", **self._consul_conf
            )
            return MysqlConf(**_consul_conf_dict)

        # 2). 从本地 local_mysql_config 的参数中取值
        if ReuseOperation.is_dict_meet_min_limit(
            dict_conf=local_mysql_conf,
            key_list=["host", "port", "user", "password", "charset", "database"],
        ):
            return MysqlConf(
                host=local_mysql_conf.get("host"),
                port=local_mysql_conf.get("port"),
                user=local_mysql_conf.get("user"),
                password=local_mysql_conf.get("password"),
                database=local_mysql_conf.get("database"),
                charset=local_mysql_conf.get("charset") or "utf8mb4",
            )


class MongoDBConfProduct(Product):
    def __init__(self, settings, consul_conf):
        self._settings = settings
        self._consul_conf = consul_conf

    def get_db_conn_conf(self) -> Union[MongoDBConf, None]:
        # 自定义 mysql 链接配置
        local_mongodb_conf = self._settings.get("LOCAL_MONGODB_CONFIG", {})
        # 是否开启应用配置管理
        app_conf_manage = self._settings.get("APP_CONF_MANAGE", False)
        if all([not local_mongodb_conf.get("database"), not app_conf_manage]):
            return None

        # 1). 如果开启应用管理，从 consul 中获取应用配置
        if app_conf_manage:
            _consul_conf_dict = ToolsForAyu.get_conf_by_consul(
                conf_name="mongodb", **self._consul_conf
            )
            return MongoDBConf(**_consul_conf_dict)

        # 2). 从本地 local_mongo_conf 的参数中取值
        if ReuseOperation.is_dict_meet_min_limit(
            dict_conf=local_mongodb_conf,
            key_list=["host", "port", "user", "password", "database"],
        ):
            return MongoDBConf(
                host=local_mongodb_conf.get("host"),
                port=local_mongodb_conf.get("port"),
                user=local_mongodb_conf.get("user"),
                password=local_mongodb_conf.get("password"),
                database=local_mongodb_conf.get("database"),
                authsource=local_mongodb_conf.get("authsource"),
            )


class MysqlConfCreator(Creator):
    def create_product(self, settings: Settings, consul_conf: dict) -> Product:
        return MysqlConfProduct(settings, consul_conf)


class MongoDBConfCreator(Creator):
    def create_product(self, settings: Settings, consul_conf: dict) -> Product:
        return MongoDBConfProduct(settings, consul_conf)


def get_spider_db_conf(
    product: Product,
) -> Union[MysqlConf, MongoDBConf, None]:
    return product.get_db_conn_conf()
