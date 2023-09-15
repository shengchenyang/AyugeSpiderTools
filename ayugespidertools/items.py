from abc import ABCMeta
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, NamedTuple, Optional, TypeVar, Union

import scrapy
from scrapy.item import Item

from ayugespidertools.common.typevars import EmptyKeyError, FieldAlreadyExistsError

__all__ = [
    "DataItem",
    "AyuItem",
]

if TYPE_CHECKING:
    from typing_extensions import Self

    # SelfType is equivalent to Self. The following are all to solve the IDE warning.
    SelfType = TypeVar("SelfType", bound=Any)
    Str = TypeVar("Str", bound=Union[str, Any])


class ScrapyItem(Item):
    """scrapy item 的标准方式"""


class DataItem(NamedTuple):
    """用于描述 item 中字段"""

    key_value: Any
    notes: str = ""


class ItemMeta(ABCMeta):
    def __new__(cls, class_name, bases, attrs):
        new_class = super().__new__(cls, class_name, bases, attrs)

        def add_field(
            self: "SelfType",
            key: "Str",
            value: Optional[Any] = None,
        ) -> None:
            """动态添加字段方法

            Args:
                self: self
                key: 需要添加的字段名
                value: 需要添加的字段对应的值
            """
            if not key:
                raise EmptyKeyError()
            if key in self._AyuItem__fields:
                raise FieldAlreadyExistsError(key)
            setattr(self, key, value)
            self._AyuItem__fields.add(key)

        def _asdict(
            self: "Self",
        ) -> Dict[str, Any]:
            """将 AyuItem 转换为 dict"""
            self._AyuItem__fields.discard("_AyuItem__fields")
            _item_dict = {key: getattr(self, key) for key in self._AyuItem__fields}
            return _item_dict

        def _asitem(
            self: "SelfType",
            assignment: bool = True,
        ) -> ScrapyItem:
            """将 AyuItem 转换为 ScrapyItem

            Args:
                assignment: 是否将 AyuItem 中的值赋值给 ScrapyItem，默认为 True

            Returns:
                new_class: 转换 ScrapyItem 后的实例
            """
            item_temp = ScrapyItem()
            for k, v in self._asdict().items():
                item_temp.fields[k] = scrapy.Field()
                if assignment:
                    item_temp[k] = v
            return item_temp

        new_class.add_field = add_field
        new_class._asdict = _asdict
        new_class._asitem = _asitem
        return new_class


@dataclass
class AyuItem(metaclass=ItemMeta):
    """用于创建和动态添加 item 字段，以及提供转换为 dict 和 ScrapyItem 的方法。

    Attributes:
        _table: 数据库表名。
        _mongo_update_rule: MongoDB 存储场景下可能需要的查重条件，默认为 None。
        __fields: 为保护字段，用于存放所有字段名，不用理会。

    Examples:
        >>> item = AyuItem(
        ...     _table="ta",
        ... )
        >>> # 获取字段；.field 和 ["field"] 两种方式
        >>> [ item._table, item["_table"] ]
        ['ta', 'ta']
        >>>
        >>> # 添加 / 修改字段，不存在则创建，存在则修改：
        >>> # 同样支持 .field 和 ["field"] 两种方式
        >>> item._table = "tab"
        >>> item["title"] = "tit"
        >>> # 也可通过 add_field 添加字段，但不能重复添加相同字段
        >>> item.add_field("num", 10)
        >>> [ item._table, item["title"], item["num"] ]
        ['tab', 'tit', 10]
        >>> item.asdict()
        {'title': 'tit', '_table': 'tab', 'num': 10}
        >>> type(item.asitem())
        <class 'ayugespidertools.items.ScrapyItem'>
        >>> # 删除字段：
        >>> del item["title"]
        >>> item
        {'_table': 'tab', 'num': 10}
    """

    _table: Optional[str] = None
    _mongo_update_rule: Optional[Dict[str, Any]] = None
    __fields: Optional[set] = None

    def __init__(
        self: "Self",
        _table: str,
        _mongo_update_rule: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """初始化 AyuItem 实例

        Args:
            _table: 数据库表名。
            _mongo_update_rule: MongoDB 存储场景下可能需要的查重条件，默认为 None。
        """
        self.__fields = set()
        if _table:
            self.__fields.add("_table")
            setattr(self, "_table", _table)
        if _mongo_update_rule:
            self.__fields.add("_mongo_update_rule")
            setattr(self, "_mongo_update_rule", _mongo_update_rule)
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.__fields.add(key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if key not in self.__fields:
            setattr(self, key, value)
            self.__fields.add(key)
        else:
            setattr(self, key, value)

    def __delitem__(self, key):
        if key not in self.__fields:
            raise KeyError(f"{key} not found")
        delattr(self, key)
        self.__fields.discard(key)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self.__fields.add(name)

    def __delattr__(self, name):
        super().__delattr__(name)
        self.__fields.discard(name)

    def __str__(self: "SelfType"):
        # 与下方 __repr__ 一样，不返回 AyuItem(field=data) 的格式
        return f"{self._asdict()}"

    def __repr__(self: "SelfType"):
        return f"{self._asdict()}"

    def fields(self):
        self.__fields.discard("_AyuItem__fields")
        return self.__fields

    def asdict(self: "SelfType") -> Dict[str, Any]:
        return self._asdict()

    def asitem(self: "Self", assignment: bool = True) -> ScrapyItem:
        return self._asitem(assignment)
