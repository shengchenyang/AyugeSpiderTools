import configparser
import json
import os
import random
from typing import TYPE_CHECKING, Any, List, Union

import pymysql
from itemadapter import ItemAdapter

from ayugespidertools.config import logger
from ayugespidertools.items import AyuItem

__all__ = [
    "ReuseOperation",
]

if TYPE_CHECKING:
    from pathlib import Path

    from scrapy.settings import BaseSettings

    from ayugespidertools.common.typevars import MysqlConf


class ReuseOperation:
    """用于存放经常复用的一些操作"""

    @staticmethod
    def fetch_local_conf(vit_dir: Union[str, "Path"], inner_settings: dict) -> dict:
        """通过本地 VIT 中的 .conf 获取所需配置，并将其添加到 inner_settings

        Args:
            vit_dir: 配置文件所在的目录
            inner_settings: inner_settings 配置

        Returns:
            inner_settings: 本库所需的配置
        """
        config_parser = configparser.ConfigParser()
        config_parser.read(f"{vit_dir}/.conf", encoding="utf-8")
        if "mysql" in config_parser:
            inner_settings["MYSQL_CONFIG"] = {
                "host": config_parser.get("mysql", "host", fallback=None),
                "port": config_parser.getint("mysql", "port", fallback=3306),
                "user": config_parser.get("mysql", "user", fallback="root"),
                "password": config_parser.get("mysql", "password", fallback=None),
                "charset": config_parser.get("mysql", "charset", fallback="utf8mb4"),
                "database": config_parser.get("mysql", "database", fallback=None),
            }
        if "mongodb" in config_parser:
            inner_settings["MONGODB_CONFIG"] = {
                "host": config_parser.get("mongodb", "host", fallback=None),
                "port": config_parser.getint("mongodb", "port", fallback=27017),
                "authsource": config_parser.get(
                    "mongodb", "authsource", fallback="admin"
                ),
                "authMechanism": config_parser.get(
                    "mongodb", "authMechanism", fallback="SCRAM-SHA-1"
                ),
                "user": config_parser.get("mongodb", "user", fallback="admin"),
                "password": config_parser.get("mongodb", "password", fallback=None),
                "database": config_parser.get("mongodb", "database", fallback=None),
            }
        if "consul" in config_parser:
            inner_settings["REMOTE_CONFIG"] = {
                "token": config_parser.get("consul", "token", fallback=None),
                "url": config_parser.get("consul", "url", fallback=None),
                "format": config_parser.get("consul", "format", fallback="json"),
                "remote_type": "consul",
            }
        elif "nacos" in config_parser:
            inner_settings["REMOTE_CONFIG"] = {
                "token": config_parser.get("nacos", "token", fallback=None),
                "url": config_parser.get("nacos", "url", fallback=None),
                "format": config_parser.get("nacos", "format", fallback="json"),
                "remote_type": "nacos",
            }
        if "kdl_dynamic_proxy" in config_parser:
            inner_settings["DYNAMIC_PROXY_CONFIG"] = {
                "proxy": config_parser.get("kdl_dynamic_proxy", "proxy", fallback=None),
                "username": config_parser.get(
                    "kdl_dynamic_proxy", "username", fallback=None
                ),
                "password": config_parser.get(
                    "kdl_dynamic_proxy", "password", fallback=None
                ),
            }
        if "kdl_exclusive_proxy" in config_parser:
            inner_settings["EXCLUSIVE_PROXY_CONFIG"] = {
                "proxy": config_parser.get(
                    "kdl_exclusive_proxy", "proxy", fallback=None
                ),
                "username": config_parser.get(
                    "kdl_exclusive_proxy", "username", fallback=None
                ),
                "password": config_parser.get(
                    "kdl_exclusive_proxy", "password", fallback=None
                ),
                "index": config_parser.getint(
                    "kdl_exclusive_proxy", "index", fallback=1
                ),
            }
        if "ali_oss" in config_parser:
            inner_settings["OSS_CONFIG"] = {
                "accesskeyid": config_parser.get(
                    "ali_oss", "accesskeyid", fallback=None
                ),
                "accesskeysecret": config_parser.get(
                    "ali_oss", "accesskeysecret", fallback=None
                ),
                "endpoint": config_parser.get("ali_oss", "endpoint", fallback=None),
                "bucket": config_parser.get("ali_oss", "bucket", fallback=None),
                "doc": config_parser.get("ali_oss", "doc", fallback=None),
            }
        if "mq" in config_parser:
            inner_settings["MQ_CONFIG"] = {
                "host": config_parser.get("mq", "host", fallback=None),
                "port": config_parser.getint("mq", "port", fallback=5672),
                "username": config_parser.get("mq", "username", fallback="guest"),
                "password": config_parser.get("mq", "password", fallback="guest"),
                "virtualhost": config_parser.get("mq", "virtualhost", fallback="/"),
                "heartbeat": config_parser.getint("mq", "heartbeat", fallback=0),
                "socket_timeout": config_parser.getint(
                    "mq", "socket_timeout", fallback=1
                ),
                "queue": config_parser.get("mq", "queue", fallback=None),
                "durable": config_parser.getboolean("mq", "durable", fallback=True),
                "exclusive": config_parser.getboolean(
                    "mq", "exclusive", fallback=False
                ),
                "auto_delete": config_parser.getboolean(
                    "mq", "auto_delete", fallback=False
                ),
                "exchange": config_parser.get("mq", "exchange", fallback=None),
                "routing_key": config_parser.get("mq", "routing_key", fallback=None),
                "content_type": config_parser.getint(
                    "mq", "content_type", fallback="text/plain"
                ),
                "delivery_mode": config_parser.getint(
                    "mq", "delivery_mode", fallback=1
                ),
                "mandatory": config_parser.getboolean("mq", "mandatory", fallback=True),
            }
        if "kafka" in config_parser:
            inner_settings["KAFKA_CONFIG"] = {
                "bootstrap_servers": config_parser.get(
                    "kafka", "bootstrap_servers", fallback="127.0.0.1:9092"
                ),
                "topic": config_parser.get("kafka", "topic", fallback=None),
                "key": config_parser.get("kafka", "key", fallback=None),
            }
        return inner_settings

    @staticmethod
    def item_to_dict(item: Union[AyuItem, dict]) -> dict:
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
    def get_files_from_path(path: str) -> list:
        """获取 path 文件夹下的所有文件，并输出以 path 为根目录的相对路径

        Args:
            path: 需要判断的文件夹路径

        Returns:
            1). path 文件夹下的文件列表
        """
        return [f.path for f in os.scandir(path) if f.is_file()]

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

    @classmethod
    def is_dict_meet_min_limit(cls, dict_conf: dict, key_list: List[str]) -> bool:
        """判断 dict_conf 是否满足 key_list 中的 key 值限定

        Args:
            dict_conf: 需要判断的参数
            key_list: dict_conf 中需要包含的 key 值列表，示例为：['proxy', 'username', 'password']

        Returns:
            1). 是否满足 key 值限制
        """
        if any([not dict_conf, not isinstance(dict_conf, dict)]):
            return False

        return all(key in dict_conf for key in key_list)

    @classmethod
    def get_items_by_keys(
        cls,
        dict_conf: dict,
        keys: List[str],
    ) -> dict:
        """获取 dict_conf 中的含有 keys 的 key 的字段

        Args:
            dict_conf: 需要处理的参数
            keys: 需要取的 key 值列表

        Returns:
            1). 取值后的 dict，或不满足请求的 False 值
        """
        # 参数先要满足最小限定，然后再取出限定的参数值；否则返回空字典
        return (
            {k: dict_conf[k] for k in keys}
            if cls.is_dict_meet_min_limit(dict_conf=dict_conf, key_list=keys)
            else {}
        )

    @classmethod
    def get_items_except_keys(cls, dict_conf, keys: List[str]) -> dict:
        """获取 dict_conf 中的不含有 keys 的 key 的字段

        Args:
            dict_conf: 需要处理的参数
            keys: 需要排除的 key 值列表

        Returns:
            1). dict_conf 排除 keys 中的键值后的值
        """
        return {k: dict_conf[k] for k in dict_conf if k not in keys}

    @classmethod
    def create_database(cls, mysql_conf: "MysqlConf") -> None:
        """创建数据库：由于这是在连接数据库，报数据库不存在错误时的场景，则需要
        新建(不指定数据库)连接创建好所需数据库即可

        Args:
            mysql_conf: pymysql 的数据库连接配置
        """
        conn = pymysql.connect(
            user=mysql_conf.user,
            password=mysql_conf.password,
            host=mysql_conf.host,
            port=mysql_conf.port,
            charset=mysql_conf.charset,
        )
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE `{mysql_conf.database}` character set {mysql_conf.charset};"
        )
        conn.close()
        logger.info(
            f"创建数据库 {mysql_conf.database} 成功，其 charset 类型是：{mysql_conf.charset}!"
        )

    @classmethod
    def dict_keys_to_lower(cls, deal_dict: dict) -> dict:
        """将 dict 中 str 类型的 key 值变成小写

        Args:
            deal_dict: 需要处理的 dict

        Returns:
            1).处理后的 dict 值
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
            1).处理后的 dict 值
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
    def get_remote_option(cls, settings: "BaseSettings") -> dict:
        """获取项目中 consul 或 nacos 的链接配置

        Args:
            settings: scrapy 的 settings 信息

        Returns:
            1). 满足最少要求的远程配置
        """
        consul_conf_dict = settings.get("REMOTE_CONFIG", {})
        return cls.get_items_by_keys(
            dict_conf=consul_conf_dict, keys=["token", "url", "format", "remote_type"]
        )

    @classmethod
    def judge_str_is_json(cls, judge_str: str) -> bool:
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
        # 也可以这样写，但不推荐
        # dict(line.split("=", 1) for line in headers_ck_str.split("; "))
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
