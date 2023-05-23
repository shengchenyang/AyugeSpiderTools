from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, Dict, Literal, NamedTuple, TypeVar, Union

import scrapy
from scrapy.item import Field, Item

ItemModeStr = Literal["Mysql", "MongoDB"]
# python 3.8 无法优雅地使用 LiteralString，以下用 Literal 代替
MysqlItemModeStr = Literal["Mysql"]
MongoDBItemModeStr = Literal["MongoDB"]
MysqlDataItemTypeVar = TypeVar("MysqlDataItemTypeVar", bound="MysqlDataItem")
MongoDataItemTypeVar = TypeVar("MongoDataItemTypeVar", bound="MongoDataItem")

__all__ = [
    "DataItem",
    "ScrapyItem",
    "ScrapyClassicItem",
    "MysqlDataItem",
    "MongoDataItem",
]


class ScrapyItem(Item):
    """scrapy item 的标准方式"""


class DataItem(NamedTuple):
    """
    用于描述 item 中字段
    """

    key_value: Any
    notes: str = ""


# item 中 alldata 的类型
AllDataType = Dict[str, Union[DataItem, Dict[str, Any], Any]]


class ScrapyClassicItem(Item):
    """
    scrapy 经典 item 示例
    """

    # 用于存放所有字段信息
    alldata: AllDataType = Field()
    # 用于存放存储的表名
    _table: str = Field()
    # 用于介绍存储场景
    _item_mode: ItemModeStr = Field()


class ItemMeta(ABCMeta):
    def __new__(cls, class_name, bases, attrs):
        new_class = super().__new__(cls, class_name, bases, attrs)

        # 动态添加字段方法
        def add_field(
            self: Union[object, MysqlDataItemTypeVar, MongoDataItemTypeVar],
            key: str = None,
            value: Any = None,
        ) -> None:
            assert key is not None, "添加字段时 key 为空！"
            setattr(self, key, value)
            self.fields.append(key)

        def _asdict(
            self,
        ) -> Dict[str, Any]:
            _item_dict = {key: getattr(self, key) for key in self.fields}
            _item_dict["_table"] = self._table
            _item_dict["_item_mode"] = self._item_mode
            if self._mongo_update_rule:
                _item_dict["_mongo_update_rule"] = self._mongo_update_rule
            return _item_dict

        def _asitem(
            self: Any,
            assignment: bool = True,
        ) -> ScrapyItem:
            item_temp = ScrapyItem()
            for k, v in self._asdict().items():
                item_temp.fields[k] = scrapy.Field()
                if any([assignment, k == "_item_mode"]):
                    item_temp[k] = v
            return item_temp

        new_class.add_field = add_field
        new_class._asdict = _asdict
        new_class._asitem = _asitem
        return new_class


@dataclass
class MysqlDataItem(metaclass=ItemMeta):
    """
    这个是 Scrapy item 的 Mysql 的存储结构
    """

    _table: str = None
    _item_mode: MysqlItemModeStr = "Mysql"

    def __init__(self, _table, _item_mode: MysqlItemModeStr = _item_mode, **kwargs):
        self._table = _table
        self._item_mode = _item_mode
        self._mongo_update_rule = None
        self.fields = []
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.fields.append(key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if key not in self.fields:
            setattr(self, key, value)
            self.fields.append(key)
        else:
            setattr(self, key, value)

    def __delitem__(self, key):
        if key in self.fields:
            delattr(self, key)
            self.fields.remove(key)

    def __str__(self: Any):
        return f"{self.__class__.__name__}({self._asdict()})"

    def asdict(self: Any):
        return self._asdict()

    def asitem(self, assignment: bool = True):
        return self._asitem(assignment)


@dataclass
class MongoDataItem(metaclass=ItemMeta):
    """
    这个是 Scrapy item 的 mongoDB 的存储结构
    """
    _table: str = None
    _item_mode: MongoDBItemModeStr = "MongoDB"
    _mongo_update_rule: Dict[str, Any] = None

    def __init__(
        self,
        _table,
        _item_mode: MongoDBItemModeStr = _item_mode,
        _mongo_update_rule: Dict[str, Any] = None,
        **kwargs,
    ):
        self._table = _table
        self._item_mode = _item_mode
        self._mongo_update_rule = _mongo_update_rule
        self.fields = []
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.fields.append(key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        if key not in self.fields:
            setattr(self, key, value)
            self.fields.append(key)
        else:
            setattr(self, key, value)

    def __delitem__(self, key):
        if key in self.fields:
            delattr(self, key)
            self.fields.remove(key)

    def __str__(self: Any):
        return f"{self.__class__.__name__}({self._asdict()})"

    def asdict(self: Any):
        return self._asdict()

    def asitem(self, assignment: bool = True):
        return self._asitem(assignment)
