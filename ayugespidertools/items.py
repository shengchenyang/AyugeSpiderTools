from __future__ import annotations

from collections.abc import MutableMapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, NoReturn

import scrapy
from scrapy.item import Item

from ayugespidertools.exceptions import EmptyKeyError, FieldAlreadyExistsError

if TYPE_CHECKING:
    from collections.abc import Iterator, KeysView
    from typing import Self

__all__ = [
    "AyuItem",
    "DataItem",
]

_MISSING = object()


class ScrapyItem(Item):
    """Standard way of scrapy items."""


class DataItem(NamedTuple):
    """Represent a field in an item.

    Attributes:
        key_value: the parameter value
        notes: a description of the parameter
    """

    key_value: Any
    notes: Any = ""


class AyuItem(MutableMapping[str, Any]):
    """Used to create AyuItem, add fields dynamically,
    and provides methods to convert to dict and ScrapyItem.

    Examples:
        >>> item = AyuItem(
        ...     _table="ta",
        ... )
        >>> # Get a field value
        >>> item["_table"]
        'ta'
        >>> # Add or modify a field. Create the key-value pair if the key does not exist;
        >>> # otherwise, update the existing value.
        >>> item["_table"] = "tab"
        >>> item["title"] = "tit"
        >>> # Fields can also be added using add_field, but duplicate keys are not allowed.
        >>> item.add_field("num", 10)
        >>> [ item["_table"], item["title"], item["num"] ]
        ['tab', 'tit', 10]
        >>> # Convert to a dictionary
        >>> item.asdict() == {'_table': 'tab', '_conflict_cols': {'id'}, 'title': 'tit', 'num': 10}
        True
        >>> # Convert to a Scrapy item
        >>> item.asitem().__class__.__name__ == "ScrapyItem"
        True
        >>> # Delete fields
        >>> item.pop("num")
        10
        >>> del item["title"]
        >>> item
        {'_table': 'tab', '_conflict_cols': {'id'}}
        >>> item.fields()
        dict_keys(['_table', '_conflict_cols'])
    """

    __slots__ = ("_data",)

    _except_keys: ClassVar[frozenset[str]] = frozenset(
        {
            "_table",
            "_update_rule",
            "_update_keys",
            "_conflict_cols",
        }
    )
    _data: dict[str, Any]

    def __init__(
        self,
        _table: DataItem | str | None = None,
        _update_rule: dict[str, Any] | None = None,
        _update_keys: set[str] | None = None,
        _conflict_cols: set[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an AyuItem instance.

        Args:
            _table: The target database table name.
            _update_rule: The criteria used to identify existing records before
                inserting data. Supported by MongoDB, MySQL, PostgreSQL, and Oracle.
            _update_keys: The fields to update when an existing record matches
                the _update_rule. If omitted, no fields are updated.
            _conflict_cols: The columns used for conflict detection in PostgreSQL
                ON CONFLICT clauses. Defaults to {"id"}.
        """
        object.__setattr__(self, "_data", kwargs)
        if _conflict_cols is None:
            _conflict_cols = {"id"}
        if _table is not None:
            self._data["_table"] = _table
        if _update_rule:
            self._data["_update_rule"] = _update_rule
        if _update_keys:
            self._data["_update_keys"] = _update_keys
        if _conflict_cols:
            self._data["_conflict_cols"] = _conflict_cols

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __getitem__(self, key: str) -> Any:
        value = self._data.get(key, _MISSING)
        if value is _MISSING:
            raise KeyError(f"Field {key!r} does not exist.")
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        self._data.pop(key, None)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getattr__(self, name: str) -> NoReturn:
        raise AttributeError(f"Use item[{name!r}] to get field value")

    def __setattr__(self, name: str, value: Any) -> NoReturn:
        raise AttributeError(f"use item[{name!r}] = value to set field value")

    def __delattr__(self, name: str) -> NoReturn:
        raise AttributeError(
            f"use del item[{name!r}] or item.pop({name!r}) to delete field value"
        )

    def add_field(self, key: str, value: Any) -> None:
        if not key:
            raise EmptyKeyError
        if key in self._data:
            raise FieldAlreadyExistsError(key)
        self._data[key] = value

    def fields(self) -> KeysView[str]:
        return self._data.keys()

    def asdict(self) -> dict[str, Any]:
        return dict(self._data)

    def asitem(self, assignment: bool = True) -> ScrapyItem:
        item = ScrapyItem()
        for key, value in self._data.items():
            item.fields[key] = scrapy.Field()
            if assignment:
                item[key] = value
        return item

    def copy(self) -> Self:
        new_item = self.__class__.__new__(self.__class__)
        object.__setattr__(new_item, "_data", dict(self._data))
        return new_item

    __copy__ = copy

    def deepcopy(self) -> Self:
        new_item = self.__class__.__new__(self.__class__)
        object.__setattr__(new_item, "_data", deepcopy(self._data))
        return new_item

    def __repr__(self) -> str:
        return repr(self._data)
