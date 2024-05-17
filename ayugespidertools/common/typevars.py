# Define your Types here
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Literal, NamedTuple, Optional, TypeVar, Union

from sqlalchemy import create_engine

if TYPE_CHECKING:
    from loguru import Logger
    from scrapy.utils.log import SpiderLoggerAdapter

    slogT = Union[Logger, SpiderLoggerAdapter]

NoneType = type(None)
I_Str = TypeVar("I_Str", int, str)
B_Str = TypeVar("B_Str", bytes, str)
I_Str_N = TypeVar("I_Str_N", int, str, NoneType)
Str_Lstr = TypeVar("Str_Lstr", str, List[str])

AiohttpRequestMethodStr = Literal[
    "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"
]
authMechanismStr = Literal[
    "SCRAM-SHA-1", "SCRAM-SHA-256", "MONGODB-CR", "MONGODB-X509", "PLAIN"
]
MysqlEngineStr = Literal["InnoDB", "MyISAM", "MEMORY", "NDB", "ARCHIVE"]
DataItemModeStr = Literal["normal", "namedtuple", "dict"]


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


class MongoDBConf(NamedTuple):
    host: str = ""
    port: int = 27017
    user: str = ""
    password: str = ""
    database: Optional[str] = None
    authsource: Optional[str] = None
    authMechanism: authMechanismStr = "SCRAM-SHA-1"
    uri: Optional[str] = None


class PostgreSQLConf(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None
    charset: str = "UTF8"


class ESConf(NamedTuple):
    hosts: str
    index_class: dict
    user: Optional[str] = None
    password: Optional[str] = None
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
    service_name: Optional[str] = None
    encoding: str = "utf8"
    thick_lib_dir: Union[bool, str] = False


class AiohttpConf(NamedTuple):
    sleep: int
    proxy: str
    proxy_auth: str
    proxy_headers: dict
    retry_times: int
    limit: int
    ssl: bool
    verify_ssl: bool
    limit_per_host: int
    allow_redirects: bool
    timeout: Optional[int] = None


class AlterItemTable(NamedTuple):
    """用于描述 AlterItem 中的 table 字段

    Attributes:
        name: table name
        notes: table name 的注释
    """

    name: str
    notes: str = ""


class AlterItem(NamedTuple):
    new_item: dict
    notes_dic: dict
    table: AlterItemTable
    is_namedtuple: bool = False


@dataclass
class AiohttpRequestArgs:
    url: Optional[str] = field(default=None)
    headers: Union[dict, None] = field(default=None)
    cookies: Union[dict, None] = field(default=None)
    method: AiohttpRequestMethodStr = field(default="GET")
    timeout: Union[int, None] = field(default=None)
    data: Union[dict, str, None] = field(default=None)
    proxy: Union[str, None] = field(default=None)
    proxy_auth: Union[str, None] = field(default=None)
    proxy_headers: Union[dict, None] = field(default=None)


class MQConf(NamedTuple):
    host: str
    port: int
    username: str
    password: str
    virtualhost: str = "/"
    heartbeat: int = 0
    socket_timeout: int = 1
    queue: Optional[str] = None
    durable: bool = True
    exclusive: bool = False
    auto_delete: bool = False
    exchange: Optional[str] = None
    routing_key: Optional[str] = None
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
    doc: Optional[str] = None
    upload_fields_suffix: str = "_file_url"
    oss_fields_prefix: str = "_"
    full_link_enable: bool = False


class FieldAlreadyExistsError(Exception):
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.message = f"字段 {field_name} 已存在！"
        super().__init__(self.message)


class EmptyKeyError(Exception):
    def __init__(self):
        self.message = "字段名不能为空！"
        super().__init__(self.message)
