#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  MultiPlexing.py
@Time    :  2022/7/12 16:53
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  用于存放经常使用的方法
"""
import copy
import json
import re
import os
import cv2
import random
import pymysql
import numpy as np
from typing import Optional, Union
from ayugespidertools.config import logger


__all__ = [
    'ReuseOperation',
]


class ReuseOperation(object):
    """
    用于存放经常复用的一些操作
    """

    @staticmethod
    def judge_file_style(media_file_or_url: str, media_type: Optional[str] = None, strict: bool = False) -> str:
        """
        判断新增图片的格式类型（此方法是为了防止图片地址格式不统一，造成图片格式提取错误）
        Args:
            media_file_or_url: 需要判断格式类型的文件或文件链接
            media_type: media 文件的类型，image，vedio，voice 等
            strict: media 是否为严格模式，严格模式下也需要仔细判断

        Returns:
            1): 文件的格式信息
        """
        if any([media_file_or_url.startswith("http"), strict]):
            image_style = ['.svg', '.png', '.jpg', '.jpeg', '.bmp', '.wav', '.mp3', '.ogg', '.flv']
            for image_format in image_style:
                if image_format in media_file_or_url:
                    return image_format[1:]

        # 否则就是文件，则返回文件后缀即可
        return media_file_or_url.split('.')[-1]

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

    # TODO: 优化此方法，修改方法名称等
    @staticmethod
    def get_voice_files(path: str) -> list:
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
    def read_image_data(bg: Union[bytes, str], tp: Union[bytes, str]):
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
            weight_data: 带权重的列表信息，示例：[{'username': 'xxxx', 'password': '******', 'weight': 8}, ...]

        Returns:
            ret: 返回当前权重的账号信息 account_arr 中的一个账号信息
        """
        total = sum(item['weight'] for item in weight_data)
        # 在 0 与权重和之间获取一个随机数
        ra = random.uniform(0, total)
        curr_sum = 0
        ret = None
        for data in weight_data:
            # 在遍历中，累加当前权重值
            curr_sum += data['weight']
            # 当随机数 <= 当前权重和时，返回权重 key
            if ra <= curr_sum:
                ret = data
                break
        return ret

    @classmethod
    def if_dict_meet_min_limit(cls, dict_config: dict, key_list: list) -> bool:
        """
        判断 dict_config 是否满足 key_list 中的 key 值限定
        Args:
            dict_config: 需要判断的参数
            key_list: dict_config 中需要包含的 key 值列表，示例为：['proxy', 'username', 'password']

        Returns:
            1). 是否满足 key 值限制
        """
        if any([not dict_config, not isinstance(dict_config, dict)]):
            return False

        # 理想中的 dict_config 参数为 dict，且其 key 要有且只有 len(key_list) 个
        ideal_keys_list = [x for x in list(dict_config.keys()) if x in key_list]
        # 如果未配置 dict_config 为 dict，且其 key 不是 key_list 中的这几个值时返回 False
        return len(ideal_keys_list) == len(key_list)

    @classmethod
    def get_items_by_keys(cls, dict_config: dict, key_list: list) -> Union[dict, bool]:
        """
        获取 dict_config 中的含有 key_list 的 key 的字段
        Args:
            dict_config: 需要处理的参数
            key_list: 需要取的 key 值列表

        Returns:
            1). 取值后的 dict，或不满足请求的 False 值
        """
        # 参数先要满足最小限定，然后再取出限定的参数值；否则直接返回 False
        return (
            {k: dict_config[k] for k in key_list}
            if cls.if_dict_meet_min_limit(
                dict_config=dict_config, key_list=key_list
            )
            else False
        )

    @classmethod
    def get_items_except_keys(cls, dict_config, key_list: list) -> dict:
        """
        获取 dict_config 中的不含有 key_list 的 key 的字段
        Args:
            dict_config: 需要处理的参数
            key_list: 需要排除的 key 值列表

        Returns:
            1). dict_config 排除 key_list 中的键值后的值
        """

        # 或者这么写
        """
        for key in key_list:
            dict(dict_config).pop(key, None)
        return dict_config
        """
        return {k: dict_config[k] for k in dict_config if k not in key_list}

    @classmethod
    def create_database(cls, pymysql_dict_config: dict):
        """
        创建数据库
        由于这是在连接数据库，报数据库不存在错误时的场景，则需要新建(不指定数据库)连接创建好所需数据库即可
        Args:
            pymysql_dict_config: pymysql 的数据库连接配置 dict

        Returns:
            None
        """
        # 判断 pymysql_dict_config 是否满足最少的 key 值
        judge_pymysql_dict_config = cls.if_dict_meet_min_limit(
            dict_config=pymysql_dict_config,
            key_list=["host", "port", "user", "password", "charset"]
        )
        assert judge_pymysql_dict_config, "创建数据库时的 pymysql 连接参数不满足条件，可能多了 database 参数，或者少了某些参数！"

        pymysql_dict_config_tmp = copy.deepcopy(pymysql_dict_config)
        if "database" in pymysql_dict_config_tmp:
            del pymysql_dict_config_tmp["database"]
        conn = pymysql.connect(**pymysql_dict_config_tmp)
        cursor = conn.cursor()
        cursor.execute(f'''CREATE DATABASE `{pymysql_dict_config["database"]}` character set {pymysql_dict_config["charset"]};''')
        conn.close()
        logger.info(f'''创建数据库 {pymysql_dict_config["database"]} 成功，类型是：{pymysql_dict_config["charset"]}!''')

    @classmethod
    def dict_keys_to_lower(cls, deal_dict: dict) -> dict:
        """
        将 dict 中 str 类型的 key 值变成小写
        Args:
            deal_dict: 需要处理的 dict

        Returns:
            1).处理后的 dict 值
        """
        str_key_to_lower_dict = {k.lower(): v for k, v in deal_dict.items() if isinstance(k, str)}
        not_str_key_dict = {k: v for k, v in deal_dict.items() if not isinstance(k, str)}
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
        str_key_to_upper_dict = {k.upper(): v for k, v in deal_dict.items() if isinstance(k, str)}
        # 找出非 str 类型的数据
        not_str_key_dict = {k: v for k, v in deal_dict.items() if not isinstance(k, str)}
        # 将大写处理的字典加上非 str 类型的 key 字段数据
        str_key_to_upper_dict.update(not_str_key_dict)
        return str_key_to_upper_dict

    @classmethod
    def get_consul_conf(cls, settings: dict) -> dict:
        """
        获取项目中的 consul 配置，且要根据项目整体情况来取出满足最少要求的 consul 配置
        Args:
            settings: scrapy 的 settings 信息

        Returns:
            consul_conf_dict_min: 满足要求的最少要求的 consul 配置
        """
        consul_conf_dict = settings.get('CONSUL_CONFIG')
        consul_conf_dict_lowered = cls.dict_keys_to_lower(consul_conf_dict)
        # 取最少需要配置的值，consul 一般情况下最少需要 host, port 和 token 共三个值
        consul_conf_dict_min = cls.get_items_by_keys(
            dict_config=consul_conf_dict_lowered,
            key_list=["host", "port", "token"]
        )
        assert consul_conf_dict_min, f"consul 配置：{consul_conf_dict} 不满足最小参数配置要求！"
        # 添加 key_values 的值，如果没有设置，则默认取全局配置中的 ENV 值
        consul_conf_dict_min["key_values"] = (
            consul_conf_dict_lowered["key_values"]
            if consul_conf_dict_lowered.get("key_values")
            else settings.get("ENV")
        )
        consul_conf_dict_min["group"] = consul_conf_dict_lowered["group"]
        return consul_conf_dict_min

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
        return {x.split("=", 1)[0].strip(): x.split("=", 1)[1].strip() for x in headers_ck_str.split(";")}

    @staticmethod
    def get_req_dict_from_scrapy(req_body_data_str: str) -> dict:
        """
        将 scrapy 请求中的 body 对象转为 dict 格式
        Args:
            req_body_data_str: scrapy 中的 body 参数

        Returns:
            1). 转化 dict 格式后的 body
        """
        return {x.split("=", 1)[0]: x.split("=", 1)[1] for x in req_body_data_str.split("&")}

    @staticmethod
    def get_array_dimension(array: list) -> int:
        """
        获取 array 的维度
        Args:
            array: 数组

        Returns:
            1).层级数
        """
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
        judge_array = isinstance(array, (frozenset, list, set, tuple,))
        return int(judge_array) and len(array) and 1 + max(map(cls.get_array_depth, array))
