# Define your TypeVar here
#
# However, it is more convenient to put the concise TypeVar in Params.py in the same directory,
# such as NoneType = type(None), etc.
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, Literal, NamedTuple, Optional, TypedDict, TypeVar, Union

__all__ = [
    "TableTemplate",
    "TableEnumTypeVar",
    "AlterItem",
    "MysqlConfig",
    "MongoDBConfig",
    "AiohttpConfig",
    "AiohttpRequestArgs",
]

AiohttpRequestMethodStr = Literal["GET", "POST"]
TableEnumTypeVar = TypeVar("TableEnumTypeVar", bound="TableEnum")

sentinel: Any = object()


class TableTemplate(TypedDict):
    # 存储表名
    value: str
    # 表注释信息
    notes: str
    # 需求表对应数据，可用于开发任务与需求任务表中任务 code 对应
    demand_code: str


@unique
class TableEnum(Enum):
    """
    数据库表枚举信息示例，用于限制存储信息类的字段及值不允许重复和修改
    """

    demo_table = TableTemplate(
        value="表名(eg: demo)",
        notes="表注释信息(eg: 示例表信息)",
        demand_code="需求表对应数据(eg: Demo_table_demand_code，此示例没有意义，需要自定义)",
    )


class MysqlConfig(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None
    charset: Optional[str] = "utf8mb4"


class MongoDBConfig(NamedTuple):
    host: str
    port: int
    user: str
    password: str
    database: Optional[str] = None
    authsource: Optional[str] = None


class AiohttpConfig(NamedTuple):
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


class AlterItem(NamedTuple):
    new_item: dict
    notes_dic: dict


@dataclass
class AiohttpRequestArgs:
    url: str = field(default=None)
    headers: Union[dict, None] = field(default=None)
    cookies: Union[dict, None] = field(default=None)
    method: AiohttpRequestMethodStr = field(default="GET")
    timeout: Union[int, None] = field(default=None)
    data: Union[dict, str, None] = field(default=None)
    proxy: Union[str, None] = field(default=None)
    proxy_auth: Union[str, None] = field(default=None)
    proxy_headers: Union[dict, None] = field(default=None)
