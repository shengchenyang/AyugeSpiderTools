from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Union

from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = [
    "Synchronize",
    "TwistedAsynchronous",
    "AsyncioAsynchronous",
    "mongodb_pipe",
]

if TYPE_CHECKING:
    from motor.core import AgnosticDatabase
    from pymongo.database import Database

    MongoDatabaseT = Union[Database, AgnosticDatabase]


class AbstractClass(ABC):
    """用于处理 mongodb pipeline 存储的模板方法类"""

    def _get_insert_data(self, item_dict: dict) -> tuple[dict, str]:
        """获取要插入的数据，将 item 中的存储数据提取出来

        Args:
            item_dict: item 的 dict 类型

        Returns:
            insert_data: 返回 dict 格式的存储数据
            table_name: item_dict 对应的 table
        """
        insert_data = ReuseOperation.get_items_except_keys(
            data=item_dict,
            keys={"_table", "_mongo_update_rule"},
        )
        table_name = item_dict["_table"]
        judge_item = next(iter(insert_data.values()))
        if ReuseOperation.is_namedtuple_instance(judge_item):
            insert_data = {v: insert_data[v].key_value for v in insert_data.keys()}
            table_name = item_dict["_table"].key_value
        return insert_data, table_name

    def process_item_template(self, item_dict: dict, db: MongoDatabaseT):
        """模板方法，用于处理 mongodb pipeline 存储的模板方法类

        Args:
            item_dict: item 的 dict 类型
            db: mongodb 数据库连接
        """
        insert_data, table_name = self._get_insert_data(item_dict)
        self._data_storage_logic(
            db=db,
            item_dict=item_dict,
            collection_name=table_name,
            insert_data=insert_data,
        )

    def _default_storage(
        self,
        db: MongoDatabaseT,
        item_dict: dict,
        collection_name: str,
        insert_data: dict,
    ):
        if not item_dict.get("_mongo_update_rule"):
            db[collection_name].insert_one(insert_data)
        else:
            db[collection_name].update_one(
                item_dict["_mongo_update_rule"], {"$set": insert_data}, upsert=True
            )

    @abstractmethod
    def _data_storage_logic(
        self,
        db: MongoDatabaseT,
        item_dict: dict,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        """数据存储逻辑，需要子类实现

        Args:
            db: mongodb 数据库连接
            item_dict: item 的 dict 类型
            collection_name: 集合名称
            insert_data: 要插入的数据
            *args: 可变参数
            **kwargs:关键字参数
        """
        raise NotImplementedError(
            "Subclasses must implement the '_data_storage_logic' method"
        )


class Synchronize(AbstractClass):
    """pipeline 同步执行 mongodb 存储的场景"""

    def _data_storage_logic(
        self,
        db: MongoDatabaseT,
        item_dict: dict,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        self._default_storage(db, item_dict, collection_name, insert_data)


class TwistedAsynchronous(AbstractClass):
    """pipeline twisted 异步执行 mongodb 存储的场景"""

    def _data_storage_logic(
        self,
        db: MongoDatabaseT,
        item_dict: dict,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        self._default_storage(db, item_dict, collection_name, insert_data)


class AsyncioAsynchronous(AbstractClass):
    """pipeline asyncio 异步执行 mongodb 存储的场景 - 使用 motor 实现"""

    async def _data_storage_logic(  # type: ignore[override]
        self,
        db: AgnosticDatabase,
        item_dict: dict,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        if not item_dict.get("_mongo_update_rule"):
            await db[collection_name].insert_one(insert_data)
        else:
            await db[collection_name].update_one(
                item_dict["_mongo_update_rule"], {"$set": insert_data}, upsert=True
            )

    async def process_item_template(self, item_dict: dict, db: MongoDatabaseT):
        insert_data, table_name = self._get_insert_data(item_dict)
        await self._data_storage_logic(
            db=db,
            item_dict=item_dict,
            collection_name=table_name,
            insert_data=insert_data,
        )


def mongodb_pipe(
    abstract_class: AbstractClass,
    item_dict: dict,
    db: MongoDatabaseT,
) -> None:
    """mongodb pipeline 存储的通用调用方法"""
    abstract_class.process_item_template(item_dict, db)
