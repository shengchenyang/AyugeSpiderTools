import copy
import json
import xml.etree.ElementTree as ET
from typing import List, Literal, Optional, Union
from urllib.parse import urlparse

import hcl2
import pandas
import requests
import yaml
from itemadapter import ItemAdapter

from ayugespidertools.common.Encryption import EncryptOperation
from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Params import Param
from ayugespidertools.common.TypeVars import MysqlConfig
from ayugespidertools.config import logger
from ayugespidertools.FormatData import DataHandle

__all__ = [
    "ToolsForAyu",
]

ConsulFormatStr = Literal["JSON", "HCL", "YAML", "XML"]
ConsulConfNameStr = Literal["MONGODB", "MYSQL"]


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
            url=f"http://{host}:{port}/v1/kv/?keys&dc=dc1&separator=%2F",
            headers=curr_consul_headers,
            verify=False,
        )
        return r.json()

    @classmethod
    def get_kvs_detail_by_consul(
        cls,
        url: str,
        token: Optional[str] = None,
    ) -> str:
        """
        获取 consul 的 key_values 的详细信息
        Args:
            token: consul token，最好只要有只读权限的 token 即可，如果未配置，则默认为 None。
            url: 当前 consul 所需配置的 url

        Returns:
            conf_value: consul 的 group 下 key_values 的详细信息
        """
        url_params = urlparse(url).query

        curr_consul_headers = copy.deepcopy(Param.consul_headers)
        curr_consul_headers["X-Consul-Token"] = token
        try:
            r = requests.get(
                url,
                headers=curr_consul_headers,
                verify=False,
                timeout=(
                    Param.requests_req_timeout,
                    Param.requests_res_timeout,
                ),
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
        ) as e:
            raise ValueError("请求 consul 超时，请检查 consul 是否正常运行!") from e
        # 判断是否返回的 raw 原始数据
        if "raw" in url_params:
            return r.text
        return EncryptOperation.base64_decode(decode_data=r.json()[0]["Value"])

    @classmethod
    def get_conf_by_consul(
        cls,
        conf_name: ConsulConfNameStr,
        url: str,
        format: ConsulFormatStr = "json",
        token: Optional[str] = None,
    ) -> dict:
        """
        获取 consul 中的 mysql 配置信息
        Args:
            conf_name: 需要获取的配置，本选项只有 "MYSQL" 和 "MONGODB"。
            token: consul token，最好只要有只读权限的 token 即可，如果未配置，则默认为 None。
            format: consul 中的配置格式，默认为 json 格式
            url: 当前 consul 所需配置的 url

        Returns:
            1). consul 应用配置中心中的 Mysql 配置信息（key 值为小写）
        """
        conf_value = cls.get_kvs_detail_by_consul(url, token)
        if format == "json":
            conf_data = json.loads(conf_value)
        elif format == "hcl":
            conf_data = hcl2.loads(conf_value)
        elif format == "yaml":
            conf_data = yaml.safe_load(conf_value)
        elif format == "xml":
            root = ET.fromstring(conf_value)
            # 将 XML 数据转换成 Python 字典
            conf_data = {}
            for child in root:
                conf_data[child.tag] = {}
                for sub_child in child:
                    conf_data[child.tag][sub_child.tag] = sub_child.text
        else:
            raise ValueError("consul 暂不支持该格式的配置")

        _conf = conf_data.get(conf_name, {})
        if not _conf:
            logger.info(f"consul 中未设置 {conf_name} 的配置信息")
        return ReuseOperation.dict_keys_to_lower(_conf)

    @classmethod
    @DataHandle.simple_deal_for_extract
    def extract_with_css(
        cls, response, query: str, get_all: bool = False, return_selector: bool = False
    ):
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
    def extract_with_xpath(
        cls, response, query: str, get_all: bool = False, return_selector: bool = False
    ):
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
    def extract_with_json(cls, json_data: dict, query: Union[str, List[str]]):
        """
        scrapy 中提取 json 数据遇到的情况
        Args:
            json_data: scrapy response 响应内容中的 json 格式数据
            query: json 提取的规则

        Returns:
            1).提取的内容
        """
        # 如果输入的提取规则参数的格式为字符；或者参数格式是个列表，但是只含有一个元素的情况时
        if any(
            [isinstance(query, str), all([isinstance(query, list), len(query) == 1])]
        ):
            if isinstance(query, str):
                return json_data.get(query, "")
            return json_data.get(query[0], "")

        # 循环取值时的处理
        for curr_q in query:
            # 这里循环时不对 json_data 的类型做判断，如果此时 json_data 类型无 get 方法，不处理
            json_data = json_data.get(curr_q, "")
            if not json_data:
                return json_data
        return json_data

    @classmethod
    def extract_with_json_rules(
        cls, json_data: dict, query_rules: List[Param.Str_Lstr]
    ):
        """
        当提取 json 某个数据时，可以在某些字段中取值，只要返回其中任意一个含有数据的值即可
        Args:
            json_data: scrapy response 响应内容中的 json 格式数据
            query_rules: json 提取的规则列表

        Returns:
            1).提取的内容
        """
        # 先判断层级，最多为 2 层
        depth_num = ReuseOperation.get_array_depth(query_rules)
        assert depth_num <= 2, "query_rules 参数错误，请输入深度最多为 2 的参数！"

        for query in query_rules:
            if extract_res := cls.extract_with_json(json_data=json_data, query=query):
                return extract_res
        return ""

    @staticmethod
    def get_collate_by_charset(mysql_conf: MysqlConfig) -> str:
        """
        根据 mysql 的 charset 获取对应默认的 collate
        Args:
            mysql_conf: mysql 连接配置

        Returns:
            collate: 排序规则
        """
        charset_collate_map = {
            # utf8mb4_unicode_ci 也是经常使用的
            "utf8mb4": "utf8mb4_general_ci",
            "utf8": "utf8_general_ci",
            "gbk": "gbk_chinese_ci",
            "latin1": "latin1_swedish_ci",
            "utf16": "utf16_general_ci",
            "utf16le": "utf16le_general_ci",
            "cp1251": "cp1251_general_ci",
            "euckr": "euckr_korean_ci",
            "greek": "greek_general_ci",
        }
        collate = charset_collate_map.get(mysql_conf.charset)
        assert (
            collate is not None
        ), f"数据库配置出现未知 charset：{mysql_conf.charset}，若抛错请查看或手动创建所需数据表！"
        return collate

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
        return {
            str(b_key, encoding="utf-8"): str(b_value_list[0], encoding="utf-8")
            for b_key, b_value_list in dict(scrapy_headers).items()
        }

    @staticmethod
    def filter_data_before_yield(
        sql: str,
        mysql_engine,
        item: Param.ScrapyItems,
    ) -> Param.ScrapyItems:
        """
        数据入库前查询是否已存在，已存在则跳过
        Args:
            sql: 判断的 sql
            mysql_engine: sqlalchemy 的 create_engine 句柄
            item: 当前 scrapy item

        Returns:
            item: 当前 scrapy item
        """
        # 数据入库逻辑
        try:
            df = pandas.read_sql(sql, mysql_engine)
            # 如果为空，说明此数据不存在于数据库，则新增
            if df.empty:
                return item

        except Exception as e:
            # 若数据库或数据表不存在时，直接返回 item 即可，会自动创建所依赖的数据库数据表及字段注释（前提是用户有对应权限，否则还是会报错）
            if any(["1146" in str(e), "1054" in str(e), "doesn't exist" in str(e)]):
                return item
            else:
                raise ValueError(f"请查看网络是否通畅，或 sql 是否正确！Error: {e}") from e
