import copy
import json
import math
import random
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import Any, List, Literal, Optional, Union
from urllib.parse import urlparse

import hcl2
import numpy as np
import pandas
import requests
import yaml

from ayugespidertools.common.encryption import EncryptOperation
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.common.typevars import MysqlConf
from ayugespidertools.config import logger
from ayugespidertools.formatdata import DataHandle

__all__ = [
    "ToolsForAyu",
    "BezierTrajectory",
]

ConsulFormatStr = Literal["json", "hcl", "yaml", "xml"]
ConsulConfNameStr = Literal[
    "mongodb",
    "mysql",
    "rabbitmq",
    "kafka",
    "dynamicproxy",
    "exclusiveproxy",
]


class ToolsForAyu:
    """这里用于存放框架所依赖的方法"""

    @classmethod
    @lru_cache(maxsize=16)
    def get_kvs_detail_by_consul(
        cls,
        url: str,
        token: Optional[str] = None,
    ) -> str:
        """获取 consul 的 key_values 的详细信息

        Args:
            token: consul token，最好只要有只读权限的 token 即可，如果未配置，则默认为 None。
            url: 当前 consul 所需配置的 url

        Returns:
            1). consul 的 group 下 key_values 的详细信息
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
        """获取 consul 中的 mysql 配置信息

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

        conf_data = ReuseOperation.dict_keys_to_lower(conf_data)
        _conf = conf_data.get(conf_name, {})
        if not _conf:
            logger.info(f"consul 中未设置 {conf_name} 的配置信息")
        return _conf

    @classmethod
    @DataHandle.simple_deal_for_extract
    def extract_with_css(
        cls, response, query: str, get_all: bool = False, return_selector: bool = False
    ):
        """使用 scrapy 的 css 提取信息

        Args:
            response: scrapy response 或者是 selector 对象
            query: css 提取的规则
            get_all: 提取模式，默认：False, 提取符合中的一个
            return_selector: 是否返回选择器对象

        Returns:
            1). 提取的内容
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
        """使用 scrapy 的 xpath 提取信息

        Args:
            response: scrapy response 或者是 selector 对象
            query: css 提取的规则
            get_all: 提取模式，默认：False, 提取符合中的一个
            return_selector: 是否返回选择器对象

        Returns:
            1). 提取的内容
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
        """scrapy 中提取 json 数据遇到的情况

        Args:
            json_data: scrapy response 响应内容中的 json 格式数据
            query: json 提取的规则

        Returns:
            1). 提取的内容
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
        """当提取 json 某个数据时，可以在某些字段中取值，只要返回其中任意一个含有数据的值即可

        Args:
            json_data: scrapy response 响应内容中的 json 格式数据
            query_rules: json 提取的规则列表

        Returns:
            1). 提取的内容
        """
        # 先判断层级，最多为 2 层
        depth_num = ReuseOperation.get_array_depth(query_rules)
        assert depth_num <= 2, "query_rules 参数错误，请输入深度最多为 2 的参数！"

        for query in query_rules:
            if extract_res := cls.extract_with_json(json_data=json_data, query=query):
                return extract_res
        return ""

    @staticmethod
    def get_collate_by_charset(mysql_conf: MysqlConf) -> str:
        """根据 mysql 的 charset 获取对应默认的 collate

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
    def first_not_none(data_lst: List[Any]) -> Any:
        """获取列表中第一个不为 None 的值

        Args:
            data_lst: 数据列表

        Returns:
            1). 第一个不为 None 的值
        """
        _res = [x for x in data_lst if x is not None]
        return _res[0] if _res else None

    @staticmethod
    def get_dict_form_scrapy_req_headers(scrapy_headers) -> dict:
        """根据 scrapy request 中的 headers 信息转化为正常的 dict 格式

        Args:
            scrapy_headers: scrapy 的 request headers 内容

        Returns:
            1). 转化 dict 后的 headers 内容
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
        """数据入库前查询是否已存在，已存在则跳过

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


class BezierTrajectory:
    """贝塞尔曲线轨迹生成器"""

    def _generate_control_points(self, track: list):
        """计算贝塞尔曲线的控制点"""
        track_len = len(track)

        def calculate_bezier_point(x):
            t = (x - track[0][0]) / (track[-1][0] - track[0][0])
            y = np.array([0, 0], dtype=np.float64)
            for s in range(len(track)):
                y += track[s] * (
                    (
                        math.factorial(track_len - 1)
                        / (math.factorial(s) * math.factorial(track_len - 1 - s))
                    )
                    * math.pow(t, s)
                    * math.pow((1 - t), track_len - 1 - s)
                )
            return y[1]

        return calculate_bezier_point

    def _type(self, type, x, length):
        numbers = []
        pin = (x[1] - x[0]) / length
        if type == 0:
            for i in range(length):
                numbers.append(i * pin)
            if pin >= 0:
                numbers = numbers[::-1]
        elif type == 1:
            for i in range(length):
                numbers.append(1 * ((i * pin) ** 2))
            numbers = numbers[::-1]
        elif type == 2:
            for i in range(length):
                numbers.append(1 * ((i * pin - x[1]) ** 2))

        elif type == 3:
            track = [
                np.array([0, 0]),
                np.array([(x[1] - x[0]) * 0.8, (x[1] - x[0]) * 0.6]),
                np.array([x[1] - x[0], 0]),
            ]
            fun = self._generate_control_points(track)
            numbers = [0]
            for i in range(1, length):
                numbers.append(fun(i * pin) + numbers[-1])
            if pin >= 0:
                numbers = numbers[::-1]
        numbers = np.abs(np.array(numbers) - max(numbers))
        normal_numbers = (
            (numbers - numbers[numbers.argmin()])
            / (numbers[numbers.argmax()] - numbers[numbers.argmin()])
        ) * (x[1] - x[0]) + x[0]
        normal_numbers[0] = x[0]
        normal_numbers[-1] = x[1]
        return normal_numbers

    def simulation(self, start, end, order=1, deviation=0, bias=0.5):
        """模拟贝塞尔曲线的绘制过程

        Args:
            start: 开始点的坐标
            end: 结束点的坐标
            order: 几阶贝塞尔曲线，越大越复杂
            deviation: 轨迹上下波动的范围
            bias: 波动范围的分布位置

        Returns:
            1). 返回一个字典 equation 对应该曲线的方程，P 对应贝塞尔曲线的影响点
        """
        start = np.array(start)
        end = np.array(end)
        shake_num = []
        if order != 1:
            e = (1 - bias) / (order - 1)
            shake_num = [[bias + e * i, bias + e * (i + 1)] for i in range(order - 1)]

        track_lst = [start]

        t = random.choice([-1, 1])
        w = 0
        for i in shake_num:
            px1 = start[0] + (end[0] - start[0]) * (
                random.random() * (i[1] - i[0]) + (i[0])
            )
            p = np.array(
                [px1, self._generate_control_points([start, end])(px1) + t * deviation]
            )
            track_lst.append(p)
            w += 1
            if w >= 2:
                w = 0
                t = -1 * t

        track_lst.append(end)
        return {
            "equation": self._generate_control_points(track_lst),
            "P": np.array(track_lst),
        }

    def gen_track(
        self,
        start: Union[np.ndarray, list],
        end: Union[np.ndarray, list],
        num: int,
        order: int = 1,
        deviation: int = 0,
        bias=0.5,
        type=0,
        shake_num=0,
        yhh=10,
    ):
        """生成轨迹数组

        Args:
            start: 开始点的坐标
            end: 结束点的坐标
            num: 返回的数组的轨迹点的数量
            order: 几阶贝塞尔曲线，越大越复杂
            deviation: 轨迹上下波动的范围
            bias: 波动范围的分布位置
            type: 0 表示均速滑动，1 表示先慢后快，2 表示先快后慢，3 表示先慢中间快后慢
            shake_num: 在终点来回摆动的次数
            yhh: 在终点来回摆动的范围

        Returns:
            1). 返回一个字典 trackArray 对应轨迹数组，P 对应贝塞尔曲线的影响点
        """
        s = []
        fun = self.simulation(start, end, order, deviation, bias)
        w = fun["P"]
        fun = fun["equation"]
        if shake_num != 0:
            track_number = round(num * 0.2 / (shake_num + 1))
            num -= num * (shake_num + 1)

            x_track_array = self._type(type, [start[0], end[0]], num)
            for i in x_track_array:
                s.append([i, fun(i)])
            dq = yhh / shake_num
            kg = 0
            ends = np.copy(end)
            for i in range(shake_num):
                if kg == 0:
                    d = np.array(
                        [
                            end[0] + (yhh - dq * i),
                            ((end[1] - start[1]) / (end[0] - start[0]))
                            * (end[0] + (yhh - dq * i))
                            + (
                                end[1]
                                - ((end[1] - start[1]) / (end[0] - start[0])) * end[0]
                            ),
                        ]
                    )
                    kg = 1
                else:
                    d = np.array(
                        [
                            end[0] - (yhh - dq * i),
                            ((end[1] - start[1]) / (end[0] - start[0]))
                            * (end[0] - (yhh - dq * i))
                            + (
                                end[1]
                                - ((end[1] - start[1]) / (end[0] - start[0])) * end[0]
                            ),
                        ]
                    )
                    kg = 0
                y = self.gen_track(
                    ends,
                    d,
                    track_number,
                    order=2,
                    deviation=0,
                    bias=0.5,
                    type=0,
                    shake_num=0,
                    yhh=10,
                )
                s += list(y["trackArray"])
                ends = d
            y = self.gen_track(
                ends,
                end,
                track_number,
                order=2,
                deviation=0,
                bias=0.5,
                type=0,
                shake_num=0,
                yhh=10,
            )
            s += list(y["trackArray"])

        else:
            x_track_array = self._type(type, [start[0], end[0]], num)
            for i in x_track_array:
                s.append([i, fun(i)])
        return {"trackArray": np.array(s), "P": w}
