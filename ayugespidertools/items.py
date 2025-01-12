from __future__ import annotations

from abc import ABCMeta
from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass
from typing import Any, NamedTuple, NoReturn

import scrapy
from scrapy.item import Item

from ayugespidertools.exceptions import EmptyKeyError, FieldAlreadyExistsError

__all__ = [
    "DataItem",
    "AyuItem",
]


class ScrapyItem(Item):
    """scrapy item 的标准方式"""

    ...


class DataItem(NamedTuple):
    """用于描述 item 中字段

    Attributes:
        key_value: 参数值
        notes: 对参数的注释
    """

    key_value: Any
    notes: Any = ""


class ItemMeta(ABCMeta):
    def __new__(
        cls, class_name: str, bases: tuple[type, ...], attrs: dict[str, Any]
    ) -> ItemMeta:
        def add_field(self, key: str, value: Any) -> None:
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

        def asdict(self) -> dict[str, Any]:
            """将 AyuItem 转换为 dict"""
            self._AyuItem__fields.discard("_AyuItem__fields")
            _item_dict = {key: getattr(self, key) for key in self._AyuItem__fields}
            return _item_dict

        def asitem(self, assignment: bool = True) -> ScrapyItem:
            """将 AyuItem 转换为 ScrapyItem

            Args:
                self: self
                assignment: 是否将 AyuItem 中的值赋值给 ScrapyItem，默认为 True

            Returns:
                1). 转换 ScrapyItem 后的实例
            """
            item_temp = ScrapyItem()
            for k, v in self.asdict().items():
                item_temp.fields[k] = scrapy.Field()
                if assignment:
                    item_temp[k] = v
            return item_temp

        attrs["add_field"] = add_field
        attrs["asdict"] = asdict
        attrs["asitem"] = asitem
        return super().__new__(cls, class_name, bases, attrs)


@dataclass
class AyuItem(MutableMapping, metaclass=ItemMeta):
    """Used to create AyuItem, add fields dynamically,
    and provides methods to convert to dict and ScrapyItem.

    Examples:
        >>> item = AyuItem(
        ...     _table="ta",
        ... )
        >>> # 获取字段
        >>> item["_table"]
        'ta'
        >>> # 添加 / 修改字段，不存在则创建，存在则修改
        >>> item["_table"] = "tab"
        >>> item["title"] = "tit"
        >>> # 也可通过 add_field 添加字段，但不能重复添加相同字段
        >>> item.add_field("num", 10)
        >>> [ item["_table"], item["title"], item["num"] ]
        ['tab', 'tit', 10]
        >>> # 转换为 dict
        >>> item.asdict() == {'title': 'tit', '_table': 'tab', 'num': 10}
        True
        >>> # 转换为 scrapy item
        >>> item.asitem().__class__.__name__ == "ScrapyItem"
        True
        >>> # 删除字段
        >>> item.pop("num")
        10
        >>> del item["title"]
        >>> item
        {'_table': 'tab'}
    """

    def __init__(
        self,
        _table: DataItem | str,
        _mongo_update_rule: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
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

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self.__fields:
            setattr(self, key, value)
            self.__fields.add(key)
        else:
            setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        if key not in self.__fields:
            raise KeyError(f"{key} not found")
        delattr(self, key)
        self.__fields.discard(key)

    def __getattr__(self, name: str) -> NoReturn:
        if name in self.__fields:
            raise AttributeError(f"Use item[{name!r}] to get field value")
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.__fields.add(name)

    def __delattr__(self, name: str) -> None:
        super().__delattr__(name)
        self.__fields.discard(name)

    def __iter__(self) -> Iterator[str]:
        return iter(self.__fields)

    def __len__(self) -> int:
        return len(self.__fields)

    def __str__(self) -> str:
        # 与下方 __repr__ 一样，不返回 AyuItem(field=data) 的格式
        return f"{self.asdict()}"

    def __repr__(self) -> str:
        return f"{self.asdict()}"

    def fields(self) -> set:
        self.__fields.discard("_AyuItem__fields")
        return self.__fields

    def add_field(self, key: str, value: Any) -> None: ...

    def asdict(self) -> dict[str, Any]: ...

    def asitem(self, assignment: bool = True) -> ScrapyItem: ...
