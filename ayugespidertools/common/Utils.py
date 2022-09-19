#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  Utils.py
@Time    :  2022/8/5 16:15
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  用于 AyugeSpiderTools 的一些通用方法，主要是用于 scrapy 扩展的一些通用方法
"""
import copy
import json
import requests
import dataclasses
import ayugespidertools.Items
from itemadapter import ItemAdapter
from ayugespidertools.config import logger
from ayugespidertools.FormatData import DataHandle
from ayugespidertools.common.Params import Param
from ayugespidertools.common.Encryption import EncryptOperation
from ayugespidertools.common.MultiPlexing import ReuseOperation


__all__ = [
    "ToolsForAyu",
]


class ToolsForAyu(object):
    """
    这里用于存放框架所依赖的方法
    """

    @classmethod
    def consul_get_all_group(cls, host: str, port: int, token: str) -> list:
        """
        获取 consul 的所有 group 信息
        Args:
            host: host
            port: port
            token: 请求 consul 所需要的 token 值

        Returns:
            1). consul 的所有 group 信息
        """
        curr_consul_headers = copy.deepcopy(Param.consul_headers)
        curr_consul_headers["X-Consul-Token"] = token
        r = requests.get(
            url=f'http://{host}:{port}/v1/kv/?keys&dc=dc1&separator=%2F',
            headers=curr_consul_headers,
            verify=False
        )
        return r.json()

    @classmethod
    def get_kvs_detail_by_consul(cls, host: str, port: int, token: str, key_values: str, group: str = None) -> dict:
        """
        获取 consul 的 key_values 的详细信息
        Args:
            host: consul host
            port: consul port
            token: consul token，最好只要有只读权限的 token 即可
            key_values: 需要获取的 consul key_values 参数值
            group: key_values 所属的 group，如果没有的话不设置此值即可

        Returns:
            conf_value: consul 的 group 下 key_values 的详细信息
        """
        if group:
            consul_url = f"http://{host}:{port}/v1/kv/{group}/{key_values}?dc=dc1"
        else:
            consul_url = f"http://{host}:{port}/v1/kv/{key_values}?dc=dc1"

        curr_consul_headers = copy.deepcopy(Param.consul_headers)
        curr_consul_headers["X-Consul-Token"] = token
        r = requests.get(consul_url, headers=curr_consul_headers, verify=False)
        conf_value = EncryptOperation.base64_decode(decode_data=r.json()[0]["Value"])
        return json.loads(conf_value)

    @classmethod
    def get_mysql_conf_by_consul(cls, host: str, port: int, token: str, key_values: str, group: str = None):
        """
        获取 consul 中的 mysql 配置信息
        Args:
            host: consul host
            port: consul port
            token: consul token，最好只要有只读权限的 token 即可
            key_values: 需要获取的 consul key_values 参数值
            group: key_values 所属的 group，如果没有的话不设置此值即可

        Returns:
            mysql_conf_lowered: consul 应用配置中心中的 Mysql 配置信息（key 值为小写）
        """
        conf_value = cls.get_kvs_detail_by_consul(host, port, token, key_values, group)
        mysql_conf = conf_value["MYSQL"] or conf_value["mysql"]
        mysql_conf_lowered = ReuseOperation.dict_keys_to_lower(mysql_conf)
        return mysql_conf_lowered

    @classmethod
    def get_mongodb_conf_by_consul(cls, host: str, port: int, token: str, key_values: str, group: str = None):
        """
        获取 consul 中的 mysql 配置信息
        Args:
            host: consul host
            port: consul port
            token: consul token，最好只要有只读权限的 token 即可
            key_values: 需要获取的 consul key_values 参数值
            group: key_values 所属的 group，如果没有的话不设置此值即可

        Returns:
            mysql_conf_lowered: consul 应用配置中心中的 Mysql 配置信息（key 值为小写）
        """
        conf_value = cls.get_kvs_detail_by_consul(host, port, token, key_values, group)
        mysql_conf = conf_value["MONGODB"] or conf_value["mongodb"]
        mysql_conf_lowered = ReuseOperation.dict_keys_to_lower(mysql_conf)
        return mysql_conf_lowered

    @classmethod
    @DataHandle.simple_deal_for_extract
    def extract_with_css(cls, response, query: str, get_all: bool = False, return_selector: bool = False):
        """
        使用 scrapy 的 css 提取信息
        Args:
            response: scrapy response 或者是 selector 对象
            query: css 提取的规则
            get_all: 提取模式，默认：False, 提取符合中的一个
            return_selector: 是否返回选择器对象

        Returns:
            1).提取的内容
        """
        if return_selector:
            return response.css(query)
        if get_all:
            return response.css(query).getall()
        else:
            return response.css(query).get(default="").strip()

    @classmethod
    @DataHandle.simple_deal_for_extract
    def extract_with_xpath(cls, response, query: str, get_all: bool = False, return_selector: bool = False):
        """
        使用 scrapy 的 xpath 提取信息
        Args:
            response: scrapy response 或者是 selector 对象
            query: css 提取的规则
            get_all: 提取模式，默认：False, 提取符合中的一个
            return_selector: 是否返回选择器对象

        Returns:
            1).提取的内容
        """
        if return_selector:
            return response.xpath(query)
        if get_all:
            return response.xpath(query).getall()
        else:
            return response.xpath(query).get(default="").strip()

    @classmethod
    @DataHandle.simple_deal_for_extract
    def extract_with_json(cls, json_data: dict, query: str or list):
        """
        scrapy 中提取 json 数据遇到的情况
        Args:
            json_data: scrapy response 响应内容中的 json 格式数据
            query: json 提取的规则

        Returns:
            1).提取的内容
        """
        # 如果输入的提取规则参数的格式为字符；或者参数格式是个列表，但是只含有一个元素的情况时
        if any([isinstance(query, str), all([isinstance(query, list), len(query) == 1])]):
            return json_data.get(query, "")

        # 循环取值时的处理
        for curr_q in query:
            json_data = json_data.get(curr_q, "")
            if not json_data:
                return json_data
        return json_data

    @staticmethod
    def get_collate_by_charset(mysql_config: dict) -> str:
        """
        根据 mysql 的 charset 获取对应 collate
        Args:
            mysql_config: mysql 连接配置

        Returns:
            collate: 排序规则
        """
        if mysql_config["charset"] == "utf8mb4":
            collate = "utf8mb4_general_ci"
        elif mysql_config["charset"] == "utf8":
            collate = "utf8_general_ci"
        else:
            raise Exception(f"数据库连接时出现未知 charset：{mysql_config['charset']}，若抛错请查看！")
        return collate

    @staticmethod
    def convert_item_to_dict(item) -> dict:
        """
        将 item 结构数据转为 dict 格式（这种转换方法太过啰嗦，已放弃，请使用下面的 convert_items_to_dict 方法）
        Args:
            item: 需要转换的参数

        Returns:
            1). 转换为 dict 格式的结果
        """
        # MongoDataItem 等其它的场景不再转换为 dict，直接使用 dataclass 即可
        if isinstance(item, ayugespidertools.Items.MysqlDataItem):
            return dataclasses.asdict(item)

        elif isinstance(item, dict):
            return item

        elif isinstance(item, ayugespidertools.Items.ScrapyClassicItem):
            return dict(item)

        else:
            logger.warning(f"出现未知 item 格式，item: {item}")
            return dict(item)

    @staticmethod
    def convert_items_to_dict(item) -> ItemAdapter:
        """
        数据容器对象的包装器，提供了一个通用接口以统一的方式处理不同类型的对象，而不管它们的底层实现如何。
        目前支持的类型有：
            1. scrapy.item.Item
            2. dict
            3. dataclass 基础类
            4. attrs 基础类
            5. pydantic 基础类
        Args:
            item: 需要转换的项目，请查看支持类型

        Returns:
            1). 转换的 ItemAdapter 结果，可以通过  obj["params"] 或 obj.get("params") 来取值
        """
        return ItemAdapter(item)

    @staticmethod
    def get_dict_form_scrapy_req_headers(scrapy_headers) -> dict:
        """
        根据 scrapy request 中的 headers 信息转化为正常的 dict 格式
        Args:
            scrapy_headers: scrapy 的 request headers 内容

        Returns:
            req_headers: 转化 dict 后的 headers 内容
        """
        req_headers = dict()
        for b_key, b_value_list in dict(scrapy_headers).items():
            req_headers[str(b_key, encoding="utf-8")] = str(b_value_list[0], encoding="utf-8")
        return req_headers
