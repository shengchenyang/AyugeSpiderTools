from __future__ import annotations

import configparser
import json
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
    """存放常用的复用方法"""

    @staticmethod
    def fetch_local_conf(vit_dir: str | Path, inner_settings: dict) -> dict:
        """通过本地 VIT 中的 .conf 获取所需配置，并将其添加到 inner_settings

        Args:
            vit_dir: 配置文件所在的目录
            inner_settings: inner_settings 配置

        Returns:
            inner_settings: 本库所需的配置
        """
        cfg = configparser.ConfigParser()
        cfg.read(f"{vit_dir}/.conf", encoding="utf-8")
        return ConfigRegistry.parse_all(cfg, inner_settings)

    @staticmethod
    def item_to_dict(item: AyuItem | dict) -> dict:
        """将 item 转换为 dict 类型；
        将 spider 中的 yield 的 item 转换为 dict 类型，方便后续处理

        Args:
            item: spider 中的 yield 的 item

        Returns:
            1). dict 类型的 item
        """
        return (
            item.asdict() if isinstance(item, AyuItem) else ItemAdapter(item).asdict()
        )

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
        """重新整合 item

        Args:
            item_dict: dict 类型的 item

        Returns:
            1). 整合后的 item
        """
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
        """判断 x 是否为 namedtuple 类型

        Args:
            x: 需要判断的参数

        Returns:
            1). 是否符合 namedtuple 类型
        """
        return isinstance(x, tuple) and hasattr(x, "_fields")

    @staticmethod
    def random_weight(weight_data: list):
        """带权重的随机取值，即在带权重的列表数据中根据权重随机取一个值

        Args:
            weight_data: 带权重的列表信息，示例：
                [{'username': 'xxxx', 'password': '******', 'weight': 8}, ...]

        Returns:
            ret: 返回当前权重列表 account_arr 中的一个值
        """
        total = sum(item["weight"] for item in weight_data)
        # 在 0 与权重和之间获取一个随机数
        ra = random.uniform(0, total)  # noqa: S311
        curr_sum = 0
        ret = None
        for data in weight_data:
            # 在遍历中，累加当前权重值
            curr_sum += data["weight"]
            # 当随机数 <= 当前权重和时，返回权重 key
            if ra <= curr_sum:
                ret = data
                break
        return ret

    @staticmethod
    def is_dict_meet_min_limit(data: dict, keys: Iterable[str]) -> bool:
        """判断 data 是否包含 keys 中所有的 key

        Args:
            data: 需要判断的参数
            keys: data 中需要包含的 key 值

        Returns:
            1). 是否满足 key 值限制
        """
        if any([not data, not isinstance(data, dict)]):
            return False

        return all(key in data for key in keys)

    @classmethod
    def get_items_by_keys(cls, data: dict, keys: Iterable[str]) -> dict:
        """获取 data 中的含有 keys 的 key 的字段

        Args:
            data: 需要处理的参数
            keys: 需要取的 key 值列表

        Returns:
            1). 取值后的 dict，或不满足请求的 False 值
        """
        if not keys:
            return {}
        return {k: v for k, v in data.items() if k in keys}

    @staticmethod
    def get_items_except_keys(data: dict[str, Any], keys: Iterable[str]) -> dict:
        """获取 data 中的不含有 keys 的 key 的字段

        Args:
            data: 需要处理的参数
            keys: 需要排除的 key 值列表

        Returns:
            1). data 排除 keys 中的键值后的值
        """
        if not keys:
            return data
        return {k: v for k, v in data.items() if k not in keys}

    @staticmethod
    def filter_none_value(data: dict[str, Any]) -> dict:
        """过滤掉 dict 中值为 None 的数据

        Args:
            data: 需要处理的参数

        Returns:
            1). data 过滤掉 dict 中值为 None 的数据
        """
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def create_database(db_conf: MysqlConf | PostgreSQLConf) -> None:
        """创建数据库：由于这是在连接数据库，报数据库不存在错误时的场景，则需要
        新建(不指定数据库)连接创建好所需数据库即可

        Args:
            db_conf: 数据库连接配置，目前支持 mysql 和 postgresql
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
            f"创建数据库 {db_conf.database} 成功，其 charset 类型是：{db_conf.charset}!"
        )

    @classmethod
    def dict_keys_to_lower(cls, deal_dict: dict) -> dict:
        """将 dict 中 str 类型的 key 值变成小写

        Args:
            deal_dict: 需要处理的 dict

        Returns:
            1). 处理后的 dict 值
        """
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
        """将 dict 中 str 类型的 key 值变成大写

        Args:
            deal_dict: 需要处理的 dict

        Returns:
            1). 处理后的 dict 值
        """
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
        """获取项目中 consul 或 nacos 的链接配置

        Args:
            settings: scrapy 的 settings 信息

        Returns:
            1). 满足最少要求的远程配置
        """
        remote_conf = settings.get("REMOTE_CONFIG", {})
        return cls.get_items_by_keys(
            data=remote_conf, keys={"token", "url", "format", "remote_type"}
        )

    @staticmethod
    def judge_str_is_json(judge_str: str) -> bool:
        """判断字符串是否为 json 格式

        Args:
            judge_str: 需要判断的字符串

        Returns:
            1). 是否为 json 格式
        """
        if not isinstance(judge_str, str):
            return False

        try:
            json.loads(judge_str)
        except Exception:
            return False
        else:
            return True

    @staticmethod
    def get_ck_dict_from_headers(headers_ck_str: str) -> dict:
        """从 headers 中的 ck str 格式转化为 dict 格式

        Args:
            headers_ck_str: request headers ck 的 str 格式

        Returns:
            1). 转化 dict 格式后的 ck
        """
        return {
            x.split("=", 1)[0].strip(): x.split("=", 1)[1].strip()
            for x in headers_ck_str.split(";")
        }

    @staticmethod
    def get_req_dict_from_scrapy(req_body_data_str: str) -> dict:
        """将 scrapy 请求中的 body 对象转为 dict 格式

        Args:
            req_body_data_str: scrapy 中的 body 参数

        Returns:
            1). 转化 dict 格式后的 body
        """
        return {
            x.split("=", 1)[0]: x.split("=", 1)[1] for x in req_body_data_str.split("&")
        }

    @classmethod
    def get_array_depth(cls, array: list) -> int:
        """获取 array 的最大层级，深度

        Args:
            array: 数组

        Returns:
            1). 最大层级，深度
        """

        """1 + max(map(depthCount,x)) if x and isinstance(x,list) else 0"""
        # 先判断是否为数组类型的元素
        judge_array = isinstance(
            array,
            (frozenset, list, set, tuple),
        )
        return (
            int(judge_array) and len(array) and 1 + max(map(cls.get_array_depth, array))
        )
