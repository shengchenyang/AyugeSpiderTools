from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from sqlalchemy.exc import OperationalError

from ayugespidertools.common.typevars import (
    DatabaseEngineClass,
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
from ayugespidertools.config import logger

try:
    from elasticsearch_dsl import connections
    from oracledb.exceptions import DatabaseError
except ImportError:
    # pip install ayugespidertools[database]  # oracledb or elasticsearch_dsl ImportError
    pass

__all__ = [
    "get_spider_conf",
    "ESConfCreator",
    "MysqlConfCreator",
    "MongoDBConfCreator",
    "MQConfCreator",
    "OracleConfCreator",
    "PostgreSQLConfCreator",
    "KafkaConfCreator",
    "DynamicProxyCreator",
    "ExclusiveProxyCreator",
    "OssConfCreator",
    "get_sqlalchemy_conf",
]

if TYPE_CHECKING:
    from elasticsearch import Elasticsearch
    from scrapy.settings import Settings
    from sqlalchemy.engine.base import Connection as SqlalchemyConnectT
    from sqlalchemy.engine.base import Engine as SqlalchemyEngineT

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

    def get_engine(
        self, db_conf: SpiderConf, db_engine_enabled: bool
    ) -> tuple[SqlalchemyEngineT | None, SqlalchemyConnectT | None]:
        """获取各个工具中对应的 sqlalchemy db_engine 和 db_engine_conn。
        需要此方法的工具有 mysql，postgresql，oracle，elasticsearch 其余的不需要。
        但其中 elasticsearch 不采用 sqlalchemy 的方式。
        """
        return None, None


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

    def get_engine(
        self, db_conf: MysqlConf, db_engine_enabled: bool
    ) -> tuple[SqlalchemyEngineT | None, SqlalchemyConnectT | None]:
        mysql_engine = mysql_engine_conn = None
        if db_engine_enabled:
            mysql_url = (
                f"mysql+pymysql://{db_conf.user}"
                f":{db_conf.password}@{db_conf.host}"
                f":{db_conf.port}/{db_conf.database}"
                f"?charset={db_conf.charset}"
            )
            try:
                mysql_engine = DatabaseEngineClass(engine_url=mysql_url).engine
                mysql_engine_conn = mysql_engine.connect()
            except OperationalError as err:
                logger.warning(f"MySQL engine enabled failed: {err}")
        return mysql_engine, mysql_engine_conn


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

    def get_engine(
        self, db_conf: PostgreSQLConf, db_engine_enabled: bool
    ) -> tuple[SqlalchemyEngineT | None, SqlalchemyConnectT | None]:
        postgres_engine = postgres_engine_conn = None
        if db_engine_enabled:
            postgres_url = (
                f"postgresql+psycopg://{db_conf.user}:{db_conf.password}"
                f"@{db_conf.host}:{db_conf.port}/{db_conf.database}"
            )
            try:
                postgres_engine = DatabaseEngineClass(engine_url=postgres_url).engine
                postgres_engine_conn = postgres_engine.connect()
            except OperationalError as err:
                logger.warning(f"PostgreSQL engine enabled failed: {err}")
        return postgres_engine, postgres_engine_conn


class ESConfProduct(Product):
    def get_conn_conf(self, settings: Settings, remote_option: dict) -> ESConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(
                conf_name="elasticsearch", **remote_option
            )
            return ESConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("ES_CONFIG")
        return ESConf(**local_conf) if local_conf else None

    def get_engine(  # type: ignore[override]
        self, db_conf: ESConf, db_engine_enabled: bool
    ) -> Elasticsearch | None:  # @override to fix mypy [override] error.
        if db_engine_enabled:
            _hosts_lst = db_conf.hosts.split(",")
            if any([db_conf.user is not None, db_conf.password is not None]):
                http_auth = (db_conf.user, db_conf.password)
            else:
                http_auth = None
            return connections.create_connection(
                hosts=_hosts_lst,
                http_auth=http_auth,
                verify_certs=db_conf.verify_certs,
                ca_certs=db_conf.ca_certs,
                client_cert=db_conf.client_cert,
                client_key=db_conf.client_key,
                ssl_assert_fingerprint=db_conf.ssl_assert_fingerprint,
            )
        return None


class OracleConfProduct(Product):
    def get_conn_conf(
        self, settings: Settings, remote_option: dict
    ) -> OracleConf | None:
        if settings.get("APP_CONF_MANAGE", False):
            remote_conf = Tools.fetch_remote_conf(conf_name="oracle", **remote_option)
            return OracleConf(**remote_conf) if remote_conf else None

        local_conf = settings.get("ORACLE_CONFIG")
        return OracleConf(**local_conf) if local_conf else None

    def get_engine(
        self, db_conf: OracleConf, db_engine_enabled: bool
    ) -> tuple[SqlalchemyEngineT | None, SqlalchemyConnectT | None]:
        oracle_engine = oracle_engine_conn = None
        if db_engine_enabled:
            oracle_url = (
                f"oracle+oracledb://{db_conf.user}:{db_conf.password}"
                f"@{db_conf.host}:{db_conf.port}/{db_conf.service_name}"
            )
            thick_mode = (
                {"lib_dir": db_conf.thick_lib_dir} if db_conf.thick_lib_dir else False
            )

            try:
                oracle_engine = DatabaseEngineClass(
                    engine_url=oracle_url,
                    thick_mode=thick_mode,
                ).engine
                oracle_engine_conn = oracle_engine.connect()
            except (OperationalError, DatabaseError) as err:
                logger.warning(f"Oracle engine enabled failed: {err}")
        return oracle_engine, oracle_engine_conn


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


def get_sqlalchemy_conf(
    creator: Creator,
    db_conf: SpiderConf,
    db_engine_enabled: bool,
) -> tuple[SqlalchemyEngineT | None, SqlalchemyConnectT | None]:
    product = creator.create_product()
    return product.get_engine(db_conf, db_engine_enabled)
