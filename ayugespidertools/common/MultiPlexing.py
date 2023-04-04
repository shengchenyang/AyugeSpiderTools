import asyncio
import json
import os
import random
import re
from typing import Any, List, Union

import cv2
import numpy as np
import pymysql
from scrapy.settings import Settings
from twisted.internet.defer import Deferred

from ayugespidertools.common.TypeVars import MysqlConfig
from ayugespidertools.config import logger

__all__ = [
    "ReuseOperation",
]


class ReuseOperation(object):
    """
    用于存放经常复用的一些操作
    """

    @staticmethod
    def as_deferred(f):
        """
        transform a Twisted Deferred to an Asyncio Future
        Args:
            f: async function

        Returns:
            1).Deferred
        """
        return Deferred.fromFuture(asyncio.ensure_future(f))

    @staticmethod
    def is_namedtuple_instance(x: Any) -> bool:
        """
        判断 x 是否为 namedtuple 类型
        Args:
            x: 需要判断的参数

        Returns:
            1). 是否符合 namedtuple 类型
        """
        return isinstance(x, tuple) and hasattr(x, "_fields")

    @staticmethod
    def get_file_name_by_url(file_url: str) -> str:
        """
        根据文件链接取出文件的名称
        Args:
            file_url: 文件链接

        Returns:
            1). 文件名称
        """
        pattern = re.compile(r""".*/(.*?)\..*?""")
        if file_name_list := pattern.findall(file_url):
            return file_name_list[0]
        return ""

    @staticmethod
    def get_files_from_path(path: str) -> list:
        """
        获取 path 文件夹下的所有文件
        Args:
            path: 需要判断的文件夹路径

        Returns:
            file_list: path 文件夹下的文件列表
        """
        # 得到文件夹下的所有文件名称
        files = os.listdir(path)
        return [file for file in files if not os.path.isdir(path + "\\" + file)]

    @staticmethod
    def get_bytes_by_file(file_path: str) -> bytes:
        """
        获取媒体文件的 bytes 内容
        Args:
            file_path: 对应文件的路径

        Returns:
            file_bytes: file_path 对应文件的 bytes 内容
        """
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        return file_bytes

    @staticmethod
    def read_image_data(
        bg: Union[bytes, str],
        tp: Union[bytes, str],
    ) -> (np.ndarray, np.ndarray):
        """
        用 opencv 读取图片数据
        Args:
            bg: 背景图片信息
            tp: 滑块图

        Returns:
            bg_cv: opencv 读取背景图片的数据
            tp_cv: opencv 读取滑块图片的数据
        """
        assert type(bg) in [str, bytes], "带缺口的背景图参数需要是全路径图片或 bytes 数据"
        assert type(tp) in [str, bytes], "滑块图参数需要是全路径图片或 bytes 数据"

        if isinstance(bg, bytes):
            bg_buf = np.frombuffer(bg, np.uint8)
            bg_cv = cv2.imdecode(bg_buf, cv2.IMREAD_ANYCOLOR)
        else:
            # 读取图片，读进来直接是 BGR 格式数据格式在 0~255
            bg_cv = cv2.imread(bg)

        if isinstance(tp, bytes):
            tp_buf = np.frombuffer(tp, np.uint8)
            tp_cv = cv2.imdecode(tp_buf, cv2.IMREAD_ANYCOLOR)
        else:
            # 0 表示采用黑白的方式读取图片
            tp_cv = cv2.imread(tp, 0)

        return bg_cv, tp_cv

    @staticmethod
    def random_weight(weight_data: list):
        """
        带权重的随机取值，即在带权重的列表数据中根据权重随机取一个值
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
        """
        判断 dict_conf 是否满足 key_list 中的 key 值限定
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
        key_list: List[str],
    ) -> Union[dict, bool]:
        """
        获取 dict_conf 中的含有 key_list 的 key 的字段
        Args:
            dict_conf: 需要处理的参数
            key_list: 需要取的 key 值列表

        Returns:
            1). 取值后的 dict，或不满足请求的 False 值
        """
        # 参数先要满足最小限定，然后再取出限定的参数值；否则直接返回 False
        return (
            {k: dict_conf[k] for k in key_list}
            if cls.is_dict_meet_min_limit(dict_conf=dict_conf, key_list=key_list)
            else False
        )

    @classmethod
    def get_items_except_keys(cls, dict_conf, key_list: List[str]) -> dict:
        """
        获取 dict_conf 中的不含有 key_list 的 key 的字段
        Args:
            dict_conf: 需要处理的参数
            key_list: 需要排除的 key 值列表

        Returns:
            1). dict_conf 排除 key_list 中的键值后的值
        """
        return {k: dict_conf[k] for k in dict_conf if k not in key_list}

    @classmethod
    def create_database(cls, mysql_conf: MysqlConfig) -> None:
        """
        创建数据库
        由于这是在连接数据库，报数据库不存在错误时的场景，则需要新建(不指定数据库)连接创建好所需数据库即可
        Args:
            mysql_conf: pymysql 的数据库连接配置

        Returns:
            None
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
        """
        将 dict 中 str 类型的 key 值变成小写
        Args:
            deal_dict: 需要处理的 dict

        Returns:
            1).处理后的 dict 值
        """
        str_key_to_lower_dict = {
            k.lower(): v for k, v in deal_dict.items() if isinstance(k, str)
        }
        not_str_key_dict = {
            k: v for k, v in deal_dict.items() if not isinstance(k, str)
        }
        # python 3.9+ 可优化为：str_key_to_lower_dict |= not_str_key_dict
        str_key_to_lower_dict.update(not_str_key_dict)
        return str_key_to_lower_dict

    @classmethod
    def dict_keys_to_upper(cls, deal_dict: dict) -> dict:
        """
        将 dict 中 str 类型的 key 值变成大写
        Args:
            deal_dict: 需要处理的 dict

        Returns:
            1).处理后的 dict 值
        """
        # 找出 str 类型的 key 字段数据，并将其大写
        str_key_to_upper_dict = {
            k.upper(): v for k, v in deal_dict.items() if isinstance(k, str)
        }
        # 找出非 str 类型的数据
        not_str_key_dict = {
            k: v for k, v in deal_dict.items() if not isinstance(k, str)
        }
        # 将大写处理的字典加上非 str 类型的 key 字段数据
        str_key_to_upper_dict.update(not_str_key_dict)
        return str_key_to_upper_dict

    @classmethod
    def get_consul_conf(cls, settings: Settings) -> dict:
        """
        获取项目中的 consul 配置，且要根据项目整体情况来取出满足最少要求的 consul 配置
        Args:
            settings: scrapy 的 settings 信息

        Returns:
            consul_conf_dict_min: 满足要求的最少要求的 consul 配置
        """
        consul_conf_dict = settings.get("CONSUL_CONFIG", {})
        consul_conf_dict_lowered = cls.dict_keys_to_lower(consul_conf_dict)
        return cls.get_items_by_keys(
            dict_conf=consul_conf_dict_lowered, key_list=["token", "url", "format"]
        )

    @classmethod
    def judge_str_is_json(cls, judge_str: str) -> bool:
        """
        判断字符串是否为 json 格式
        Args:
            judge_str: 需要判断的字符串

        Returns:
            1）.是否为 json 格式
        """
        if not isinstance(judge_str, str):
            return False

        try:
            json.loads(judge_str)
        except Exception as e:
            return False
        else:
            return True

    @staticmethod
    def get_ck_dict_from_headers(headers_ck_str: str) -> dict:
        """
        从 headers 中的 ck str 格式转化为 dict 格式
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
        """
        将 scrapy 请求中的 body 对象转为 dict 格式
        Args:
            req_body_data_str: scrapy 中的 body 参数

        Returns:
            1). 转化 dict 格式后的 body
        """
        return {
            x.split("=", 1)[0]: x.split("=", 1)[1] for x in req_body_data_str.split("&")
        }

    @staticmethod
    def get_array_dimension(array: list) -> int:
        """
        获取 array 的维度
        Args:
            array: 数组

        Returns:
            1).层级数
        """
        # 其实直接返回 len(array) 即可
        return len(np.array(array).shape)

    @classmethod
    def get_array_depth(cls, array: list) -> int:
        """
        获取 array 的最大层级，深度
        Args:
            array: 数组

        Returns:
            1).最大层级，深度
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
