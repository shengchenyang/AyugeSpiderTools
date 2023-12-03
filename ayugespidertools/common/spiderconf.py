from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple, TypeVar

from sqlalchemy.exc import OperationalError

from ayugespidertools.common.typevars import (
    DatabaseEngineClass,
    DynamicProxyConf,
    ExclusiveProxyConf,
    KafkaConf,
    MongoDBConf,
    MQConf,
    MysqlConf,
    PostgreSQLConf,
)
from ayugespidertools.common.utils import ToolsForAyu

__all__ = [
    "get_spider_conf",
    "MysqlConfCreator",
    "MongoDBConfCreator",
    "MQConfCreator",
    "PostgreSQLConfCreator",
    "KafkaConfCreator",
    "DynamicProxyCreator",
    "ExclusiveProxyCreator",
    "get_sqlalchemy_conf",
]

if TYPE_CHECKING:
    from scrapy.settings import Settings
    from sqlalchemy.engine.base import Connection as SqlalchemyConnectT
    from sqlalchemy.engine.base import Engine as SqlalchemyEngineT

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
    def get_conn_conf(
        self, settings: "Settings", remote_option: dict
    ) -> Optional[SpiderConf]:
        """获取各个工具链接配置信息"""
        pass

    @abstractmethod
    def get_engine(
        self, db_conf: SpiderConf, db_engine_enabled: bool
    ) -> Tuple[Optional["SqlalchemyEngineT"], Optional["SqlalchemyConnectT"]]:
        """获取各个工具中对应的 sqlalchemy db_engine 和 db_engine_conn。
        需要此方法的工具有 mysql，postgresql，mongodb，oracle，其余的不需要。
        """
        pass


class Creator(ABC):
    @abstractmethod
    def create_product(self) -> Product:
        pass


class MysqlConfProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        # 1). 优先从远程配置中取值
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="mysql", **remote_option
            )
            return MysqlConf(**remote_conf) if remote_conf else None

        # 2). 从本地参数中取值
        local_conf = settings.get("MYSQL_CONFIG")
        return MysqlConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        if db_engine_enabled:
            mysql_url = (
                f"mysql+pymysql://{db_conf.user}"
                f":{db_conf.password}@{db_conf.host}"
                f":{db_conf.port}/{db_conf.database}"
                f"?charset={db_conf.charset}"
            )
            mysql_engine = DatabaseEngineClass(engine_url=mysql_url).engine
            try:
                mysql_engine_conn = mysql_engine.connect()
            except OperationalError:
                mysql_engine_conn = None
            return mysql_engine, mysql_engine_conn
        return None, None


class MongoDBConfProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="mongodb", **remote_option
            )
            return MongoDBConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("MONGODB_CONFIG")
        return MongoDBConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        pass


class PostgreSQLConfProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="postgresql", **remote_option
            )
            return PostgreSQLConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("POSTGRESQL_CONFIG")
        return PostgreSQLConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        if db_engine_enabled:
            postgres_url = (
                f"postgresql+psycopg://{db_conf.user}:{db_conf.password}"
                f"@{db_conf.host}:{db_conf.port}/{db_conf.database}"
            )
            postgres_engine = DatabaseEngineClass(engine_url=postgres_url).engine
            try:
                postgres_engine_conn = postgres_engine.connect()
            except OperationalError:
                postgres_engine_conn = None
            return postgres_engine, postgres_engine_conn
        return None, None


class MQConfProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="rabbitmq", **remote_option
            )
            return MQConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("MQ_CONFIG")
        return MQConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        pass


class KafkaConfProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="kafka", **remote_option
            )
            return KafkaConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("KAFKA_CONFIG")
        return KafkaConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        pass


class DynamicProxyProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="dynamicproxy", **remote_option
            )
            return DynamicProxyConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("DYNAMIC_PROXY_CONFIG")
        return DynamicProxyConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        pass


class ExclusiveProxyProduct(Product):
    def get_conn_conf(self, settings: "Settings", remote_option: dict):
        if _ := settings.get("APP_CONF_MANAGE", False):
            remote_conf = ToolsForAyu.fetch_remote_conf(
                conf_name="exclusiveproxy", **remote_option
            )
            return ExclusiveProxyConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("EXCLUSIVE_PROXY_CONFIG")
        return ExclusiveProxyConf(**local_conf) if local_conf else None

    def get_engine(self, db_conf: SpiderConf, db_engine_enabled: bool):
        pass


class MysqlConfCreator(Creator):
    def create_product(self) -> Product:
        return MysqlConfProduct()


class MongoDBConfCreator(Creator):
    def create_product(self) -> Product:
        return MongoDBConfProduct()


class PostgreSQLConfCreator(Creator):
    def create_product(self) -> Product:
        return PostgreSQLConfProduct()


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


def get_spider_conf(
    creator: Creator, settings: "Settings", remote_option: dict
) -> Optional[SpiderConf]:
    product = creator.create_product()
    return product.get_conn_conf(settings, remote_option)


def get_sqlalchemy_conf(
    creator: Creator,
    db_conf: SpiderConf,
    db_engine_enabled: bool,
) -> Tuple["SqlalchemyEngineT", "SqlalchemyConnectT"]:
    product = creator.create_product()
    return product.get_engine(db_conf, db_engine_enabled)
