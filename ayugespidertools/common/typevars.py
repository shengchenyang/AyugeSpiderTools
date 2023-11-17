# Define your TypeVar here
from dataclasses import dataclass, field
from typing import List, Literal, NamedTuple, Optional, TypeVar, Union

NoneType = type(None)
I_Str = TypeVar("I_Str", int, str)
B_Str = TypeVar("B_Str", bytes, str)
I_Str_N = TypeVar("I_Str_N", int, str, NoneType)
Str_Lstr = TypeVar("Str_Lstr", str, List[str])

AiohttpRequestMethodStr = Literal["GET", "POST"]
authMechanismStr = Literal[
    "SCRAM-SHA-1", "SCRAM-SHA-256", "MONGODB-CR", "MONGODB-X509", "PLAIN"
]


class MysqlConf(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None
    charset: str = "utf8mb4"


class MongoDBConf(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None
    authsource: Optional[str] = None
    authMechanism: authMechanismStr = "SCRAM-SHA-1"


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
    timeout: int
    allow_redirects: bool


class AlterItem(NamedTuple):
    new_item: dict
    notes_dic: dict


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
    bootstrap_servers: list
    topic: str
    key: str


class FieldAlreadyExistsError(Exception):
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.message = f"字段 {field_name} 已存在！"
        super().__init__(self.message)


class EmptyKeyError(Exception):
    def __init__(self):
        self.message = "字段名不能为空！"
        super().__init__(self.message)
