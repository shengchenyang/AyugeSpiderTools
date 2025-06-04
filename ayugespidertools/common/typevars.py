# Define your Types here
from __future__ import annotations

import threading
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, TypeVar, Union

from sqlalchemy import create_engine
from yarl import URL

if TYPE_CHECKING:
    import asyncio
    from ssl import SSLContext

    from loguru import Logger
    from scrapy.utils.log import SpiderLoggerAdapter

    slogT = Union[Logger, SpiderLoggerAdapter]

NoneType = type(None)
I_Str = TypeVar("I_Str", int, str)
B_Str = TypeVar("B_Str", bytes, str)
I_Str_N = TypeVar("I_Str_N", int, str, None)
Str_Lstr = TypeVar("Str_Lstr", str, list[str])
_SENTINEL = Enum("_SENTINEL", "sentinel")
sentinel = _SENTINEL.sentinel
StrOrURL = Union[str, URL]

InsertPrefixStr = Literal["INSERT IGNORE", "INSERT"]
OracleAuthenticationModesStr = Literal[
    "DEFAULT",
    "PRELIM",
    "SYSASM",
    "SYSBKP",
    "SYSDBA",
    "SYSDGD",
    "SYSKMT",
    "SYSOPER",
    "SYSRAC",
]
AiohttpRequestMethodStr = Literal[
    "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"
]
authMechanismStr = Literal[
    "SCRAM-SHA-1", "SCRAM-SHA-256", "MONGODB-CR", "MONGODB-X509", "PLAIN"
]
MysqlEngineStr = Literal["InnoDB", "MyISAM", "MEMORY", "NDB", "ARCHIVE"]
DataItemModeStr = Literal["normal", "namedtuple", "dict"]


class PortalTag(str, Enum):
    LIBRARY = "Ayuge"
    THIRD_PARTY = "ThirdParty"
    DEFAULT = "Default"
    OTHER = "Other"


class DatabaseSingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, engine_url, *args, **kwargs):
        if engine_url not in cls._instances:
            with cls._lock:
                if engine_url not in cls._instances:
                    instance = super().__call__(engine_url, *args, **kwargs)
                    cls._instances[engine_url] = instance
        return cls._instances[engine_url]


class DatabaseEngineClass(metaclass=DatabaseSingletonMeta):
    """database engine 单例模式：同一个 engine_url 只能存在一个实例"""

    def __init__(self, engine_url, *args, **kwargs):
        self.engine = create_engine(
            engine_url, pool_pre_ping=True, pool_recycle=3600 * 7, *args, **kwargs
        )


class MysqlConf(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: str
    engine: MysqlEngineStr = "InnoDB"
    charset: str = "utf8mb4"
    collate: str = "utf8mb4_general_ci"
    odku_enable: bool = False
    insert_ignore: bool = False

    @property
    def insert_prefix(self) -> InsertPrefixStr:
        return "INSERT IGNORE" if self.insert_ignore else "INSERT"


class MongoDBConf(NamedTuple):
    host: str = ""
    port: int = 27017
    user: str = ""
    password: str = ""
    database: str | None = None
    authsource: str | None = None
    authMechanism: authMechanismStr = "SCRAM-SHA-1"
    uri: str | None = None


class PostgreSQLConf(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: str | None = None
    charset: str = "UTF8"


class ESConf(NamedTuple):
    hosts: str
    index_class: dict
    user: str | None = None
    password: str | None = None
    init: bool = False
    verify_certs: bool = False
    ca_certs: str = None
    client_cert: str = None
    client_key: str = None
    ssl_assert_fingerprint: str = None


class OracleConf(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    service_name: str | None = None
    encoding: str = "utf8"
    thick_lib_dir: bool | str = False
    authentication_mode: OracleAuthenticationModesStr = "DEFAULT"


class AiohttpConf(NamedTuple):
    # 这些是对应 aiohttp.TCPConnector 中的配置
    verify_ssl: bool | None = None
    fingerprint: bytes | None = None
    use_dns_cache: bool | None = None
    ttl_dns_cache: int | None = None
    family: int | None = None
    ssl_context: SSLContext | None = None
    ssl: bool | None = None
    local_addr: tuple[str, int] | None = None
    resolver: str | None = None
    keepalive_timeout: float | object | None = None
    force_close: bool | None = None
    limit: int | None = None
    limit_per_host: int | None = None
    enable_cleanup_closed: bool | None = None
    loop: asyncio.AbstractEventLoop | None = None
    timeout_ceil_threshold: float | None = None
    happy_eyeballs_delay: float | None = None
    interleave: int | None = None

    # 这些是一些全局中需要的配置，其它的参数都在 ClientSession.request 中赋值
    sleep: int | None = None
    retry_times: int | None = None
    timeout: int | None = None


class AlterItemTable(NamedTuple):
    """用于描述 AlterItem 中的 table 字段

    Attributes:
        name: table name
        notes: table name 的注释
    """

    name: str
    notes: str = ""


class AlterItem(NamedTuple):
    new_item: dict[str, Any]
    notes_dic: dict[str, str]
    table: AlterItemTable
    is_namedtuple: bool = False


class MQConf(NamedTuple):
    host: str
    port: int
    username: str
    password: str
    virtualhost: str = "/"
    heartbeat: int = 0
    socket_timeout: int = 1
    queue: str | None = None
    durable: bool = True
    exclusive: bool = False
    auto_delete: bool = False
    exchange: str | None = None
    routing_key: str | None = None
    content_type: str = "text/plain"
    delivery_mode: int = 1
    mandatory: bool = True


class DynamicProxyConf(NamedTuple):
    proxy: str
    username: str
    password: str


class ExclusiveProxyConf(NamedTuple):
    proxy: str
    username: str
    password: str
    index: int


class KafkaConf(NamedTuple):
    bootstrap_servers: str
    topic: str
    key: str


class OssConf(NamedTuple):
    access_key: str
    access_secret: str
    endpoint: str
    bucket: str
    doc: str | None = None
    upload_fields_suffix: str = "_file_url"
    oss_fields_prefix: str = "_"
    full_link_enable: bool = False
