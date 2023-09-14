# Define your TypeVar here
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import (
    TYPE_CHECKING,
    List,
    Literal,
    NamedTuple,
    Optional,
    TypedDict,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from itemadapter import ItemAdapter

NoneType = type(None)
I_Str = TypeVar("I_Str", int, str)
B_Str = TypeVar("B_Str", bytes, str)
I_Str_N = TypeVar("I_Str_N", int, str, NoneType)
Str_Lstr = TypeVar("Str_Lstr", str, List[str])

AiohttpRequestMethodStr = Literal["GET", "POST"]
TableEnumTypeVar = TypeVar("TableEnumTypeVar", bound="TableEnum")
ItemAdapterType = TypeVar("ItemAdapterType", bound="ItemAdapter")


class TableTemplate(TypedDict):
    # 存储表名
    value: str
    # 表注释信息
    notes: str
    # 需求表对应数据，可用于开发任务与需求任务表中任务 code 对应
    demand_code: str


@unique
class TableEnum(Enum):
    """数据库表枚举信息示例，用于限制存储信息类的字段及值不允许重复和修改"""

    demo_table = TableTemplate(
        value="表名(eg: demo)",
        notes="表注释信息(eg: 示例表信息)",
        demand_code="需求表对应数据(eg: Demo_table_demand_code，此示例没有意义，需要自定义)",
    )


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
