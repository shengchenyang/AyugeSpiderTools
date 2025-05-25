from __future__ import annotations

import configparser
import json
import random
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import pymysql
from itemadapter import ItemAdapter

from ayugespidertools.common.params import Param
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
        if "mysql" in cfg:
            mysql_section = cfg["mysql"]
            _charset = mysql_section.get("charset", "utf8mb4")
            inner_settings["MYSQL_CONFIG"] = {
                "host": mysql_section.get("host", "localhost"),
                "port": mysql_section.getint("port", 3306),
                "user": mysql_section.get("user", ""),
                "password": mysql_section.get("password", ""),
                "charset": _charset,
                "database": mysql_section.get("database", ""),
                "engine": mysql_section.get("engine", "InnoDB"),
                "collate": mysql_section.get(
                    "collate",
                    Param.charset_collate_map.get(_charset, "utf8mb4_general_ci"),
                ),
                "odku_enable": mysql_section.getboolean("odku_enable", False),
                "insert_ignore": mysql_section.getboolean("insert_ignore", False),
            }
        if "mongodb:uri" in cfg:
            inner_settings["MONGODB_CONFIG"] = {
                "uri": cfg.get("mongodb:uri", "uri", fallback=None)
            }
        elif "mongodb" in cfg:
            mongodb_section = cfg["mongodb"]
            inner_settings["MONGODB_CONFIG"] = {
                "host": mongodb_section.get("host", "localhost"),
                "port": mongodb_section.getint("port", 27017),
                "authsource": mongodb_section.get("authsource", "admin"),
                "authMechanism": mongodb_section.get("authMechanism", "SCRAM-SHA-1"),
                "user": mongodb_section.get("user", "admin"),
                "password": mongodb_section.get("password", None),
                "database": mongodb_section.get("database", None),
            }
        if "postgresql" in cfg:
            postgres_section = cfg["postgresql"]
            inner_settings["POSTGRESQL_CONFIG"] = {
                "host": postgres_section.get("host", "localhost"),
                "port": postgres_section.getint("port", 5432),
                "user": postgres_section.get("user", "postgres"),
                "password": postgres_section.get("password", ""),
                "database": postgres_section.get("database", ""),
                "charset": postgres_section.get("charset", "UTF8"),
            }
        if "elasticsearch" in cfg:
            es_section = cfg["elasticsearch"]
            inner_settings["ES_CONFIG"] = {
                "hosts": es_section.get("hosts", None),
                "index_class": json.loads(
                    es_section.get(
                        "index_class", '{"settings":{"number_of_shards": 2}}'
                    )
                ),
                "user": es_section.get("user", None),
                "password": es_section.get("password", None),
                "init": es_section.getboolean("init", False),
                "verify_certs": es_section.getboolean("verify_certs", False),
                "ca_certs": es_section.get("ca_certs", None),
                "client_cert": es_section.get("client_cert", None),
                "client_key": es_section.get("client_key", None),
                "ssl_assert_fingerprint": es_section.get(
                    "ssl_assert_fingerprint", None
                ),
            }
        if "oracle" in cfg:
            oracle_section = cfg["oracle"]
            inner_settings["ORACLE_CONFIG"] = {
                "host": oracle_section.get("host", "localhost"),
                "port": oracle_section.getint("port", 1521),
                "user": oracle_section.get("user", None),
                "password": oracle_section.get("password", None),
                "service_name": oracle_section.get("service_name", None),
                "encoding": oracle_section.get("encoding", "utf8"),
                "thick_lib_dir": oracle_section.get("thick_lib_dir", False),
                "authentication_mode": oracle_section.get(
                    "authentication_mode", "DEFAULT"
                ),
            }
        if "consul" in cfg:
            consul_section = cfg["consul"]
            inner_settings["REMOTE_CONFIG"] = {
                "token": consul_section.get("token", None),
                "url": consul_section.get("url", None),
                "format": consul_section.get("format", "json"),
                "remote_type": "consul",
            }
        elif "nacos" in cfg:
            nacos_section = cfg["nacos"]
            inner_settings["REMOTE_CONFIG"] = {
                "token": nacos_section.get("token", None),
                "url": nacos_section.get("url", None),
                "format": nacos_section.get("format", "json"),
                "remote_type": "nacos",
            }
        if "kdl_dynamic_proxy" in cfg:
            kdl_dynamic_section = cfg["kdl_dynamic_proxy"]
            inner_settings["DYNAMIC_PROXY_CONFIG"] = {
                "proxy": kdl_dynamic_section.get("proxy", None),
                "username": kdl_dynamic_section.get("username", None),
                "password": kdl_dynamic_section.get("password", None),
            }
        if "kdl_exclusive_proxy" in cfg:
            kdl_exclusive_section = cfg["kdl_exclusive_proxy"]
            inner_settings["EXCLUSIVE_PROXY_CONFIG"] = {
                "proxy": kdl_exclusive_section.get("proxy", None),
                "username": kdl_exclusive_section.get("username", None),
                "password": kdl_exclusive_section.get("password", None),
                "index": kdl_exclusive_section.getint("index", 1),
            }
        if "mq" in cfg:
            mq_section = cfg["mq"]
            _queue = mq_section.get("queue", None)
            inner_settings["MQ_CONFIG"] = {
                "host": mq_section.get("host", "localhost"),
                "port": mq_section.getint("port", 5672),
                "username": mq_section.get("username", "guest"),
                "password": mq_section.get("password", "guest"),
                "virtualhost": mq_section.get("virtualhost", "/"),
                "heartbeat": mq_section.getint("heartbeat", 0),
                "socket_timeout": mq_section.getint("socket_timeout", 1),
                "queue": _queue,
                "durable": mq_section.getboolean("durable", True),
                "exclusive": mq_section.getboolean("exclusive", False),
                "auto_delete": mq_section.getboolean("auto_delete", False),
                "exchange": mq_section.get("exchange", ""),
                "routing_key": mq_section.get("routing_key", _queue),
                "content_type": mq_section.getint("content_type", "text/plain"),
                "delivery_mode": mq_section.getint("delivery_mode", 1),
                "mandatory": mq_section.getboolean("mandatory", True),
            }
        if "kafka" in cfg:
            kafka_section = cfg["kafka"]
            inner_settings["KAFKA_CONFIG"] = {
                "bootstrap_servers": kafka_section.get(
                    "bootstrap_servers", "127.0.0.1:9092"
                ),
                "topic": kafka_section.get("topic", None),
                "key": kafka_section.get("key", None),
            }
        if "oss:ali" in cfg:
            oss_section = cfg["oss:ali"]
            inner_settings["OSS_CONFIG"] = {
                "access_key": oss_section.get("access_key", None),
                "access_secret": oss_section.get("access_secret", None),
                "endpoint": oss_section.get("endpoint", None),
                "bucket": oss_section.get("bucket", None),
                "doc": oss_section.get("doc", None),
                "upload_fields_suffix": oss_section.get(
                    "upload_fields_suffix", "_file_url"
                ),
                "oss_fields_prefix": oss_section.get("oss_fields_prefix", "_"),
                "full_link_enable": oss_section.getboolean("full_link_enable", False),
            }
        return inner_settings

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
    def reshape_item(cls, item_dict: dict[str, Any]) -> AlterItem:
        """重新整合 item

        Args:
            item_dict: dict 类型的 item

        Returns:
            1). 整合后的 item
        """
        new_item = {}
        notes_dic = {}
        is_namedtuple = False

        insert_data = cls.get_items_except_keys(
            data=item_dict, keys={"_mongo_update_rule", "_table"}
        )
        judge_item = next(iter(insert_data.values()))
        if cls.is_namedtuple_instance(judge_item):
            is_namedtuple = True
            _table_name = item_dict["_table"].key_value
            _table_notes = item_dict["_table"].notes
            table_info = AlterItemTable(_table_name, _table_notes)
            for key, value in insert_data.items():
                new_item[key] = value.key_value
                notes_dic[key] = value.notes

        else:
            _table_name = item_dict["_table"]
            table_info = AlterItemTable(_table_name, "")
            for key, value in insert_data.items():
                new_item[key] = value
                notes_dic[key] = ""

        return AlterItem(new_item, notes_dic, table_info, is_namedtuple)

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
        ra = random.uniform(0, total)
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
                        f"CREATE DATABASE {db_conf.database} WITH ENCODING {db_conf.charset};"
                    )

        else:
            assert False, f"Invalid db_conf type: {type(db_conf)}"
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
            (
                frozenset,
                list,
                set,
                tuple,
            ),
        )
        return (
            int(judge_array) and len(array) and 1 + max(map(cls.get_array_depth, array))
        )
