from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.items import AyuItem

__all__ = [
    "AsyncStorageHandler",
    "SyncStorageHandler",
    "get_insert_data",
    "store_async_process",
    "store_process",
]

if TYPE_CHECKING:
    from motor.core import AgnosticDatabase
    from pymongo.database import Database


def get_insert_data(item_dict: dict) -> tuple[dict, str]:
    insert_data = ReuseOperation.get_items_except_keys(
        item_dict, keys=AyuItem._except_keys
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
        update_rule = item_dict.get("_update_rule") or item_dict.get(
            "_mongo_update_rule"
        )
        if update_rule:
            update_doc = {}
            update_keys = item_dict.get("_update_keys") or item_dict.get(
                "_mongo_update_keys"
            )
            if update_keys:
                set_data = ReuseOperation.get_items_by_keys(
                    data=insert_data, keys=update_keys
                )
                update_doc["$set"] = set_data
            else:
                set_data = {}
            update_doc["$setOnInsert"] = ReuseOperation.get_items_except_keys(
                data=insert_data, keys=set_data
            )
            db[collection].update_one(
                filter=update_rule, update=update_doc, upsert=True
            )
        else:
            db[collection].insert_one(insert_data)


class AsyncStorageHandler:
    @staticmethod
    async def store(
        db: AgnosticDatabase, item_dict: dict, collection: str, insert_data: dict
    ) -> None:
        update_rule = item_dict.get("_update_rule") or item_dict.get(
            "_mongo_update_rule"
        )
        if update_rule:
            update_doc = {}
            update_keys = item_dict.get("_update_keys") or item_dict.get(
                "_mongo_update_keys"
            )
            if update_keys:
                set_data = ReuseOperation.get_items_by_keys(
                    data=insert_data, keys=update_keys
                )
                update_doc["$set"] = set_data
            else:
                set_data = {}
            update_doc["$setOnInsert"] = ReuseOperation.get_items_except_keys(
                data=insert_data, keys=set_data
            )
            await db[collection].update_one(
                filter=update_rule, update=update_doc, upsert=True
            )
        else:
            await db[collection].insert_one(insert_data)
