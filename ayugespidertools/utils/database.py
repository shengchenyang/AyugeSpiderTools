from __future__ import annotations

import asyncio
import hashlib
import threading
import urllib.parse
from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar

import aiomysql
import pymysql
from motor.motor_asyncio import AsyncIOMotorClient

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import (
    ESConf,
    KafkaConf,
    MongoDBConf,
    MQConf,
    MysqlConf,
    OracleConf,
    OssConf,
    PortalTag,
    PostgreSQLConf,
)
from ayugespidertools.exceptions import UnsupportedError
from ayugespidertools.mongoclient import MongoDbBase

try:
    import aio_pika
    import asyncpg
    import oracledb
    import psycopg
    from asyncpg.pool import Pool as PGPool  # noqa: TC002
    from elasticsearch_dsl import connections
except ImportError:
    # pip install ayugespidertools[database]
    pass

__all__ = [
    "ElasticSearchPortal",
    "MongoDBAsyncPortal",
    "MongoDBPortal",
    "MysqlAsyncPortal",
    "MysqlPortal",
    "OracleAsyncPortal",
    "OraclePortal",
    "PostgreSQLAsyncPortal",
    "PostgreSQLPortal",
    "RabbitMQAsyncPortal",
]

if TYPE_CHECKING:
    from aio_pika.abc import AbstractRobustConnection
    from aiomysql import Pool as MysqlPool
    from motor.motor_asyncio import AsyncIOMotorDatabase
    from psycopg.connection import Connection as PsycopgConnection
    from pymongo import MongoClient, database
    from pymysql.connections import Connection as PymysqlConnection

DataBaseConf = TypeVar(
    "DataBaseConf",
    MysqlConf,
    ESConf,
    MongoDBConf,
    MQConf,
    KafkaConf,
    OracleConf,
    OssConf,
    PostgreSQLConf,
)

T = TypeVar("T")


def unique_key(data: dict | NamedTuple, referer: str, tag: PortalTag) -> str:
    if ReuseOperation.is_namedtuple_instance(data):
        data_dct = data._asdict()
        items = data_dct.items()
    elif isinstance(data, dict):
        items = data.items()
    else:
        raise TypeError(f"Unsupported type {type(data)}")

    sorted_items = sorted(items)
    joined_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    final_str = f"{tag}_{referer}_{joined_str}"
    return hashlib.sha1(final_str.encode("utf-8")).hexdigest()  # noqa: S324


class PortalSingletonMeta(type, Generic[T, DataBaseConf]):
    _instances: dict[str, T] = {}
    _lock = threading.Lock()

    def __call__(
        cls: type[T],
        db_conf: DataBaseConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
        *args,
        **kwargs,
    ) -> T:
        if not singleton:
            return super().__call__(db_conf, tag, singleton, *args, **kwargs)  # type: ignore[misc]

        unique_id = unique_key(data=db_conf, referer=cls.__name__, tag=tag)
        if unique_id not in cls._instances:
            with cls._lock:
                if unique_id not in cls._instances:
                    instance = super().__call__(db_conf, tag, *args, **kwargs)  # type: ignore[misc]
                    cls._instances[unique_id] = instance
        return cls._instances[unique_id]


class MysqlPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: MysqlConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        pymysql_conn_args = {
            "user": db_conf.user,
            "password": db_conf.password,
            "host": db_conf.host,
            "port": db_conf.port,
            "database": db_conf.database,
            "charset": db_conf.charset,
        }
        self.conn = pymysql.connect(**pymysql_conn_args)

    def connect(self) -> PymysqlConnection:
        return self.conn


class MysqlAsyncPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: MysqlConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        self.db_conf = db_conf
        self._pool: MysqlPool | None = None
        self._init_lock = asyncio.Lock()
        self.singleton = singleton

    async def _create_pool(self) -> MysqlPool:
        return await aiomysql.create_pool(
            host=self.db_conf.host,
            port=self.db_conf.port,
            user=self.db_conf.user,
            password=self.db_conf.password,
            db=self.db_conf.database,
            charset=self.db_conf.charset,
            cursorclass=aiomysql.DictCursor,
            autocommit=True,
        )

    async def connect(self) -> MysqlPool:
        if not self.singleton:
            return await self._create_pool()

        if self._pool is None:
            async with self._init_lock:
                if self._pool is None:
                    self._pool = await self._create_pool()
        return self._pool

    async def close(self) -> None:
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()


class ElasticSearchPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: ESConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        _hosts_lst = db_conf.hosts.split(",")
        if any([db_conf.user is not None, db_conf.password is not None]):
            http_auth = (db_conf.user, db_conf.password)
        else:
            http_auth = None
        self.conn = connections.create_connection(
            hosts=_hosts_lst,
            http_auth=http_auth,
            verify_certs=db_conf.verify_certs,
            ca_certs=db_conf.ca_certs,
            client_cert=db_conf.client_cert,
            client_key=db_conf.client_key,
            ssl_assert_fingerprint=db_conf.ssl_assert_fingerprint,
        )

    def connect(self):
        return self.conn


class MongoDBPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: MongoDBConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        self.client, self.db = MongoDbBase.connects(**db_conf._asdict())

    def get_client(self) -> MongoClient:
        return self.client

    def connect(self) -> database.Database:
        return self.db


class MongoDBAsyncPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: MongoDBConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        if db_conf.uri is not None:
            _mongo_uri = db_conf.uri
        else:
            _encoded_pwd = urllib.parse.quote_plus(db_conf.password)
            _mongo_uri = (
                f"mongodb://{db_conf.user}:{_encoded_pwd}@{db_conf.host}:{db_conf.port}/"
                f"{db_conf.database}?authSource={db_conf.authsource}"
                f"&authMechanism={db_conf.authMechanism}"
            )
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(_mongo_uri)
        self.db: AsyncIOMotorDatabase = self.client.get_database()

    def get_client(self) -> AsyncIOMotorClient:
        return self.client

    def connect(self) -> AsyncIOMotorDatabase:
        return self.db

    def close(self):
        self.client.close()


class RabbitMQPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: MQConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ): ...

    def connect(self): ...


class RabbitMQAsyncPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: MQConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        self.db_conf = db_conf
        if "," in self.db_conf.host:
            raise UnsupportedError(
                "The host parameter in AyuAsyncMQPipeline cannot contain commas. "
                "Modify the host parameter in the [mq] section of the .conf file."
            )

    async def connect(self) -> AbstractRobustConnection:
        return await aio_pika.connect_robust(
            host=self.db_conf.host,
            port=self.db_conf.port,
            login=self.db_conf.username,
            password=self.db_conf.password,
            virtualhost=self.db_conf.virtualhost,
        )


class KafkaPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: KafkaConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ): ...

    def connect(self): ...


class OraclePortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: OracleConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ) -> None:
        if db_conf.authentication_mode not in {
            "DEFAULT",
            "PRELIM",
            "SYSASM",
            "SYSBKP",
            "SYSDBA",
            "SYSDGD",
            "SYSKMT",
            "SYSOPER",
            "SYSRAC",
        }:
            raise ValueError("OracleDB requires the authentication modes parameter.")

        oracle_authentication_mode = getattr(
            oracledb, f"AUTH_MODE_{db_conf.authentication_mode}", 0
        )
        if oracle_thick_lib_dir := db_conf.thick_lib_dir:
            oracledb.init_oracle_client(oracle_thick_lib_dir)

        self.conn = oracledb.connect(
            user=db_conf.user,
            password=db_conf.password,
            host=db_conf.host,
            port=db_conf.port,
            service_name=db_conf.service_name,
            mode=oracle_authentication_mode,
        )

    def connect(self) -> oracledb.Connection:
        return self.conn


class OracleAsyncPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: OracleConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ) -> None:
        if db_conf.authentication_mode not in {
            "DEFAULT",
            "PRELIM",
            "SYSASM",
            "SYSBKP",
            "SYSDBA",
            "SYSDGD",
            "SYSKMT",
            "SYSOPER",
            "SYSRAC",
        }:
            raise ValueError("OracleDB requires the authentication modes parameter.")

        oracle_authentication_mode = getattr(
            oracledb, f"AUTH_MODE_{db_conf.authentication_mode}", 0
        )
        if oracle_thick_lib_dir := db_conf.thick_lib_dir:
            oracledb.init_oracle_client(oracle_thick_lib_dir)

        self.pool = oracledb.create_pool_async(
            user=db_conf.user,
            password=db_conf.password,
            host=db_conf.host,
            port=db_conf.port,
            service_name=db_conf.service_name,
            mode=oracle_authentication_mode,
        )

    def connect(self) -> oracledb.AsyncConnectionPool:
        return self.pool

    async def close(self) -> None:
        await self.pool.close()


class OSSPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: OssConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ): ...

    def connect(self): ...


class PostgreSQLPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: PostgreSQLConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        self.conn = psycopg.connect(
            user=db_conf.user,
            password=db_conf.password,
            host=db_conf.host,
            port=db_conf.port,
            dbname=db_conf.database,
        )

    def connect(self) -> PsycopgConnection:
        return self.conn

    def close(self):
        self.conn.close()


class PostgreSQLAsyncPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: PostgreSQLConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
        self.db_conf = db_conf
        self._pool: PGPool | None = None
        self._init_lock = asyncio.Lock()
        self.singleton = singleton

    async def _create_pool(self) -> PGPool:
        return await asyncpg.create_pool(
            f"postgresql://{self.db_conf.user}:{self.db_conf.password}"
            f"@{self.db_conf.host}:{self.db_conf.port}/{self.db_conf.database}"
        )

    async def connect(self) -> PGPool:
        if not self.singleton:
            return await self._create_pool()

        if self._pool is None:
            async with self._init_lock:
                if self._pool is None:
                    self._pool = await self._create_pool()
        return self._pool

    async def close(self):
        if self._pool:
            await self._pool.close()
