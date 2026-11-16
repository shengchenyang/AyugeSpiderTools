from __future__ import annotations

import configparser
import random
from typing import TYPE_CHECKING, Any

import pymysql
from itemadapter import ItemAdapter

from ayugespidertools.common.confighandler import ConfigRegistry
from ayugespidertools.common.typevars import (
    AlterItem,
    AlterItemTable,
    MysqlConf,
    PostgreSQLConf,
)
from ayugespidertools.config import logger
from ayugespidertools.items import AyuItem

try:
    import psycopg
except ImportError:
    # pip install ayugespidertools[database]
    pass

__all__ = [
    "ReuseOperation",
]

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from scrapy.settings import BaseSettings


class ReuseOperation:
    @staticmethod
    def fetch_local_conf(vit_dir: str | Path, inner_settings: dict) -> dict:
        """Obtain the required configuration from the .conf file in your local
        VIT and add it to inner_settings.

        Args:
            vit_dir: path to the local VIT directory
            inner_settings: internal settings

        Returns:
            inner_settings: the settings required by this library.
        """
        cfg = configparser.ConfigParser()
        cfg.read(f"{vit_dir}/.conf", encoding="utf-8")
        return ConfigRegistry.parse_all(cfg, inner_settings)

    @staticmethod
    def item_to_dict(item: AyuItem | dict) -> dict:
        if isinstance(item, dict):
            return item
        if isinstance(item, AyuItem):
            return item.asdict()
        return ItemAdapter(item).asdict()

    @classmethod
    def get_insert_data(cls, item_dict: dict) -> tuple[dict, str]:
        insert_data = cls.get_items_except_keys(item_dict, keys=AyuItem._except_keys)
        table_name = item_dict["_table"]
        judge_item = next(iter(insert_data.values()))
        if cls.is_namedtuple_instance(judge_item):
            insert_data = {k: v.key_value for k, v in insert_data.items()}
            table_name = table_name.key_value
        return insert_data, table_name

    @classmethod
    def reshape_item(cls, item_dict: dict[str, Any]) -> AlterItem:
        insert_data = cls.get_items_except_keys(
            data=item_dict, keys=AyuItem._except_keys
        )
        judge_item = next(iter(insert_data.values()))
        update_rule = item_dict.get("_update_rule", {})
        update_keys = item_dict.get("_update_keys", set())
        conflict_cols = item_dict.get("_conflict_cols", set())
        if cls.is_namedtuple_instance(judge_item):
            if _table := item_dict.get("_table"):
                _table_name = _table.key_value
                _table_notes = _table.notes
            else:
                _table_name = _table_notes = ""

            table_info = AlterItemTable(_table_name, _table_notes)
            new_item = {k: v.key_value for k, v in insert_data.items()}
            notes_dic = {k: v.notes for k, v in insert_data.items()}
            return AlterItem(
                new_item=new_item,
                notes_dic=notes_dic,
                table=table_info,
                is_namedtuple=True,
                update_rule=update_rule,
                update_keys=update_keys,
                conflict_cols=conflict_cols,
            )

        _table_name = item_dict.get("_table", "")
        table_info = AlterItemTable(_table_name)
        notes_dic = dict.fromkeys(insert_data, "")
        return AlterItem(
            new_item=insert_data,
            notes_dic=notes_dic,
            table=table_info,
            is_namedtuple=False,
            update_rule=update_rule,
            update_keys=update_keys,
            conflict_cols=conflict_cols,
        )

    @staticmethod
    def is_namedtuple_instance(x: Any) -> bool:
        """Check whether x is a namedtuple instance.

        Args:
            x: the object to check

        Returns:
            whether x is a namedtuple instance.
        """
        return isinstance(x, tuple) and hasattr(x, "_fields")

    @staticmethod
    def random_weight(weight_data: list):
        """Randomly select an item from a weighted list based on its weight.

        Args:
            weight_data: a list of weighted items. For example:
                [{'username': 'xxxx', 'password': '******', 'weight': 8}, ...]

        Returns:
            an item randomly selected from the weighted list.
        """
        total = sum(item["weight"] for item in weight_data)
        # generate a random number between 0 and the total weight.
        ra = random.uniform(0, total)  # noqa: S311
        curr_sum = 0
        ret = None
        for data in weight_data:
            # accumulate the weights while iterating.
            curr_sum += data["weight"]
            # return the item when the random number falls within the cumulative weight.
            if ra <= curr_sum:
                ret = data
                break
        return ret

    @staticmethod
    def is_dict_meet_min_limit(data: dict, keys: Iterable[str]) -> bool:
        """Check whether data contains all the specified keys.

        Args:
            data: the dictionary to check
            keys: the keys that must be present in the dictionary

        Returns:
            whether the dictionary contains all the specified keys.
        """
        if any([not data, not isinstance(data, dict)]):
            return False

        return all(key in data for key in keys)

    @classmethod
    def get_items_by_keys(cls, data: dict, keys: Iterable[str] | None) -> dict:
        """Extract the specified key-value pairs from data.

        Args:
            data: the dictionary to process
            keys: the keys to extract from the dictionary

        Returns:
            a dictionary containing the matching key-value pairs, or an empty
            dictionary if no keys are specified.
        """
        if not keys:
            return {}
        return {k: v for k, v in data.items() if k in keys}

    @staticmethod
    def get_items_except_keys(data: dict[str, Any], keys: Iterable[str] | None) -> dict:
        """Exclude the specified keys from data.

        Args:
            data: the dictionary to process
            keys: the keys to exclude from the dictionary

        Returns:
            a dictionary containing the remaining key-value pairs after exclusion.
        """
        if not keys:
            return data
        return {k: v for k, v in data.items() if k not in keys}

    @staticmethod
    def filter_none_value(data: dict[str, Any]) -> dict:
        """Filter out key-value pairs with None values from a dictionary.

        Args:
            data: the dictionary to process

        Returns:
            a dictionary containing only key-value pairs with non-None values.
        """
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def create_database(db_conf: MysqlConf | PostgreSQLConf) -> None:
        """Create the database if it does not exist.

        When a database connection fails because the specified database does not
        exist, establish a connection without specifying a database and create
        the required database.

        Args:
            db_conf: database connection configuration. currently supports MySQL
            and PostgreSQL.
        """
        if isinstance(db_conf, MysqlConf):
            with pymysql.connect(
                user=db_conf.user,
                password=db_conf.password,
                host=db_conf.host,
                port=db_conf.port,
                charset=db_conf.charset,
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{db_conf.database}` character set {db_conf.charset};"
                    )

        elif isinstance(db_conf, PostgreSQLConf):
            with psycopg.connect(
                user=db_conf.user,
                password=db_conf.password,
                host=db_conf.host,
                port=db_conf.port,
            ) as conn:
                with conn.cursor() as cur:
                    conn.autocommit = True
                    cur.execute(
                        f"CREATE DATABASE {db_conf.database} WITH ENCODING {db_conf.charset};"  # type: ignore[arg-type]
                    )

        else:
            raise TypeError(f"Invalid db_conf type: {type(db_conf)}")
        logger.info(
            f"Database {db_conf.database} created successfully with charset：{db_conf.charset}!"
        )

    @classmethod
    def dict_keys_to_lower(cls, deal_dict: dict) -> dict:
        """Convert all string keys in a dictionary to lowercase recursively."""
        key_to_lower_dict = {}
        for key, value in deal_dict.items():
            if isinstance(value, dict):
                if isinstance(key, str):
                    key_to_lower_dict[key.lower()] = cls.dict_keys_to_lower(value)
                else:
                    key_to_lower_dict[key] = cls.dict_keys_to_lower(value)
            elif isinstance(key, str):
                key_to_lower_dict[key.lower()] = value
            else:
                key_to_lower_dict[key] = value
        return key_to_lower_dict

    @classmethod
    def dict_keys_to_upper(cls, deal_dict: dict) -> dict:
        """Convert all string keys in a dictionary to uppercase."""
        key_to_upper_dict = {}
        for key, value in deal_dict.items():
            if isinstance(value, dict):
                if isinstance(key, str):
                    key_to_upper_dict[key.upper()] = cls.dict_keys_to_upper(value)
                else:
                    key_to_upper_dict[key] = cls.dict_keys_to_upper(value)
            elif isinstance(key, str):
                key_to_upper_dict[key.upper()] = value
            else:
                key_to_upper_dict[key] = value
        return key_to_upper_dict

    @classmethod
    def get_remote_option(cls, settings: BaseSettings) -> dict:
        remote_conf = settings.get("REMOTE_CONFIG", {})
        return cls.get_items_by_keys(
            data=remote_conf, keys={"token", "url", "format", "remote_type"}
        )

    @staticmethod
    def get_ck_dict_from_headers(headers_ck_str: str) -> dict:
        """Convert a cookie string from request headers into a dictionary.

        Args:
            headers_ck_str: the cookie string from request headers

        Returns:
            a dictionary containing the parsed cookies.
        """
        return {
            x.split("=", 1)[0].strip(): x.split("=", 1)[1].strip()
            for x in headers_ck_str.split(";")
        }

    @staticmethod
    def get_req_dict_from_scrapy(req_body_data_str: str) -> dict:
        """Convert a Scrapy request body string into a dictionary.

        Args:
            req_body_data_str: the request body string from Scrapy

        Returns:
            a dictionary containing the parsed request body parameters.
        """
        return {
            x.split("=", 1)[0]: x.split("=", 1)[1] for x in req_body_data_str.split("&")
        }

    @classmethod
    def get_array_depth(cls, array: list) -> int:
        """Get the maximum nesting depth of an array.

        Args:
            array: the array to measure

        Returns:
            the maximum nesting depth.
        """

        """1 + max(map(depthCount,x)) if x and isinstance(x,list) else 0"""
        # check whether the element is a sequence or set
        judge_array = isinstance(
            array,
            frozenset | list | set | tuple,
        )
        return (
            int(judge_array) and len(array) and 1 + max(map(cls.get_array_depth, array))
        )
