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
from ayugespidertools.mongoclient import MongoDbBase

try:
    import asyncpg
    import oracledb
    import psycopg
    from asyncpg.pool import Pool as PGPool
except ImportError:
    # pip install ayugespidertools[database]
    pass

__all__ = [
    "MysqlPortal",
    "MysqlAsyncPortal",
    "MongoDBPortal",
    "MongoDBAsyncPortal",
    "OraclePortal",
    "OracleAsyncPortal",
    "PostgreSQLPortal",
    "PostgreSQLAsyncPortal",
    "ElasticSearchPortal",
]

if TYPE_CHECKING:
    from aiomysql import Pool
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
    return hashlib.sha1(final_str.encode("utf-8")).hexdigest()


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
        self._pool: Pool | None = None
        self._lock = asyncio.Lock()
        self.singleton = singleton

    async def _create_pool(self):
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

    async def connect(self) -> Pool:
        if not self.singleton:
            return await self._create_pool()

        if self._pool is None:
            async with self._lock:
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
    ): ...

    def connect(self): ...


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
    ):
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

    def connect(self):
        return self.conn


class OracleAsyncPortal(metaclass=PortalSingletonMeta):
    def __init__(
        self,
        db_conf: OracleConf,
        tag: PortalTag = PortalTag.DEFAULT,
        singleton: bool = False,
    ):
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

    def connect(self):
        return self.pool


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

    async def connect(self) -> PGPool:
        self._pool = await asyncpg.create_pool(
            f"postgresql://{self.db_conf.user}:{self.db_conf.password}"
            f"@{self.db_conf.host}:{self.db_conf.port}/{self.db_conf.database}"
        )
        return self._pool

    async def close(self):
        await self._pool.close()
