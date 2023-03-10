# Define your TypeVar here
#
# However, it is more convenient to put the concise TypeVar in Params.py in the same directory,
# such as NoneType = type(None), etc.
from enum import Enum, unique
from typing import TypedDict, TypeVar

__all__ = ["TableTemplate", "TableEnumTypeVar"]

TableEnumTypeVar = TypeVar("TableEnumTypeVar", bound="TableEnum")


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