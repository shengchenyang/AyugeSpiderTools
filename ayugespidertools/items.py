from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, Dict, Literal, NamedTuple, TypeVar, Union

import scrapy
from scrapy.item import Field, Item

ItemModeStr = Literal["Mysql", "MongoDB"]
# python 3.8 无法优雅地使用 LiteralString，以下用 Literal 代替
MysqlItemModeStr = Literal["Mysql"]
MongoDBItemModeStr = Literal["MongoDB"]
AyuItemTypeVar = TypeVar("AyuItemTypeVar", bound="AyuItem")

__all__ = [
    "DataItem",
    "ScrapyItem",
    "ScrapyClassicItem",
    "AyuItem",
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
            self: Union[object, AyuItemTypeVar],
            key: str = None,
            value: Any = None,
        ) -> None:
            assert key is not None, "添加字段时 key 为空！"
            setattr(self, key, value)
            self.fields.append(key)

        def _asdict(
            self,
        ) -> Dict[str, Any]:
            """
            将 AyuItem 转换为 dict
            """
            _item_dict = {key: getattr(self, key) for key in self.fields}
            _item_dict["_table"] = self._table
            if self._mongo_update_rule:
                _item_dict["_mongo_update_rule"] = self._mongo_update_rule
            return _item_dict

        def _asitem(
            self: Any,
            assignment: bool = True,
        ) -> ScrapyItem:
            """
            将 AyuItem 转换为 ScrapyItem
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
    """
    这个是 Scrapy item 的 Mysql 的存储结构

    Attributes:
        _table (str): 数据库表名。
        _mongo_update_rule (Dict[str, Any]): MongoDB 存储场景下可能需要的查重条件，默认为 None。

    Examples:
        >>> item = AyuItem(
        >>>     _table="test_table",
        >>>     title="test_title",
        >>>     _mongo_update_rule={"title": "test_title"},
        >>> )
        >>> item._table
        'test_table'
        >>> item.asdict()
        {'title': 'test_title', '_table': 'test_table', '_mongo_update_rule': {'title': 'test_title'}}
        >>> type(item.asitem())
        <class 'ayugespidertools.items.ScrapyItem'>
    """

    _table: str = None
    _mongo_update_rule: Dict[str, Any] = None

    def __init__(
        self,
        _table: str,
        _mongo_update_rule: Dict[str, Any] = None,
        **kwargs,
    ):
        """
        初始化 AyuItem 实例。

        Args:
            _table: 数据库表名。
            _mongo_update_rule: MongoDB 存储场景下可能需要的查重条件，默认为 None。
        """
        self._table = _table
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
