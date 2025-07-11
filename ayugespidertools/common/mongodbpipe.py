from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = [
    "get_insert_data",
    "store_process",
    "store_async_process",
    "SyncStorageHandler",
    "AsyncStorageHandler",
]

if TYPE_CHECKING:
    from motor.core import AgnosticDatabase
    from pymongo.database import Database


def get_insert_data(item_dict: dict) -> tuple[dict, str]:
    insert_data = ReuseOperation.get_items_except_keys(
        item_dict, keys={"_table", "_mongo_update_rule"}
    )
    table_name = item_dict["_table"]
    judge_item = next(iter(insert_data.values()))
    if ReuseOperation.is_namedtuple_instance(judge_item):
        insert_data = {k: v.key_value for k, v in insert_data.items()}
        table_name = table_name.key_value
    return insert_data, table_name


class SyncStorage(Protocol):
    @staticmethod
    def store(
        db: Database, item_dict: dict, collection: str, insert_data: dict
    ) -> None: ...


class AsyncStorage(Protocol):
    @staticmethod
    async def store(
        db: AgnosticDatabase, item_dict: dict, collection: str, insert_data: dict
    ) -> None: ...


def store_process(item_dict: dict, db: Database, handler: SyncStorage):
    insert_data, collection = get_insert_data(item_dict)
    handler.store(db, item_dict, collection, insert_data)


async def store_async_process(
    item_dict: dict, db: AgnosticDatabase, handler: AsyncStorage
):
    insert_data, collection = get_insert_data(item_dict)
    await handler.store(db, item_dict, collection, insert_data)


class SyncStorageHandler:
    @staticmethod
    def store(
        db: Database, item_dict: dict, collection: str, insert_data: dict
    ) -> None:
        if not item_dict.get("_mongo_update_rule"):
            db[collection].insert_one(insert_data)
        else:
            db[collection].update_one(
                item_dict["_mongo_update_rule"], {"$set": insert_data}, upsert=True
            )


class AsyncStorageHandler:
    @staticmethod
    async def store(
        db: AgnosticDatabase, item_dict: dict, collection: str, insert_data: dict
    ) -> None:
        if not item_dict.get("_mongo_update_rule"):
            await db[collection].insert_one(insert_data)
        else:
            await db[collection].update_one(
                item_dict["_mongo_update_rule"], {"$set": insert_data}, upsert=True
            )
