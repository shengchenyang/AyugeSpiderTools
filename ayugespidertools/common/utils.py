import json
import random
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Union
from urllib.parse import urlparse

import requests

from ayugespidertools.common.encryption import EncryptOperation
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.config import logger
from ayugespidertools.extras.ext import AppConfManageMixin
from ayugespidertools.formatdata import DataHandle

__all__ = ["ToolsForAyu"]

if TYPE_CHECKING:
    from scrapy.http import Response

    from ayugespidertools.common.typevars import MysqlConf, Str_Lstr

RemoteFormatStr = Literal["json", "hcl", "yaml", "xml"]
RemoteTypeStr = Literal["consul", "nacos"]
RemoteConfNameStr = Literal[
    "mongodb",
    "mysql",
    "rabbitmq",
    "kafka",
    "dynamicproxy",
    "exclusiveproxy",
]


class ToolsForAyu(AppConfManageMixin):
    """这里用于存放框架所依赖的方法"""

    @classmethod
    @lru_cache(maxsize=16)
    def get_remote_kvs(
        cls,
        url: str,
        remote_type: RemoteTypeStr = "consul",
        token: Optional[str] = None,
    ) -> str:
        """获取远程配置中的 key_values 信息

        Args:
            url: 获取 kvs 所需的 url
            remote_type: 配置类型
            token: consul token or nacos token; nacos 的 token 值直接在 url 中构造即可

        Returns:
            1). 远程配置中 key_values 的详细信息
        """
        headers = {"X-Consul-Token": token} if remote_type == "consul" else None
        try:
            r = requests.get(
                url,
                headers=headers,
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
            raise ValueError(f"请求远程配置 {remote_type} api 超时!") from e

        url_params = urlparse(url).query
        if remote_type == "consul":
            if "raw" in url_params:
                return r.text
            return EncryptOperation.base64_decode(decode_data=r.json()[0]["Value"])
        return r.text

    @classmethod
    def fetch_remote_conf(
        cls,
        conf_name: RemoteConfNameStr,
        url: str,
        format: RemoteFormatStr = "json",
        remote_type: RemoteTypeStr = "consul",
        token: Optional[str] = None,
    ) -> dict:
        """获取远程中的项目配置信息

        Args:
            conf_name: 需要获取的配置
            token: consul token or nacos token
            format: 远程配置中的格式，默认为 json 格式
            remote_type: 配置类型
            url: 获取远程配置所需的 url

        Returns:
            1). 远程应用配置中心中的配置信息（key 值为小写）
        """
        conf_value = cls.get_remote_kvs(url, remote_type, token)
        if format == "json":
            conf_data = json.loads(conf_value)
        elif format == "xml":
            conf_data = cls.xml_parser(conf_value)
        elif format == "yaml":
            conf_data = cls.yaml_parser(conf_value)
        elif format == "hcl":
            conf_data = cls.hcl_parser(conf_value)
        else:
            raise ValueError(f"{conf_name} 暂不支持该格式的配置")

        _conf = conf_data.get(conf_name, {})
        if not _conf:
            logger.info(f"远程配置 {remote_type} 中未设置 {conf_name}")
        return _conf

    @classmethod
    @DataHandle.simple_deal_for_extract
    def extract_with_css(
        cls,
        response: "Response",
        query: str,
        get_all: bool = False,
        return_selector: bool = False,
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
        cls,
        response: "Response",
        query: str,
        get_all: bool = False,
        return_selector: bool = False,
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
    def extract_with_json_rules(cls, json_data: dict, query_rules: List["Str_Lstr"]):
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
    def get_collate_by_charset(mysql_conf: "MysqlConf") -> str:
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

    @classmethod
    def get_data_urls_by_img(cls, mediatype: str, data: Union[bytes, str]) -> str:
        """根据本地、远程或 bytes 内容的图片生成 Data URLs 格式的数据
        Data URLs 格式示例:
            data:image/png;base64,iVB...
            data:text/html,%3Ch1%3EHello%2C%20World%21%3C%2Fh1%3E
        关于 Data URLs 更多的描述，其参考文档: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs

        Args:
            mediatype: MIME 类型字符串，例如 'image/jpeg' JPEG 图像文件。
                如果省略，则默认为 text/plain;charset=US-ASCII
            data: 用于获取其 base64 编码的二进制数据
                参数格式可以为全路径图片，或 bytes 内容

        Returns:
            1). Data URLs 格式数据
        """
        assert type(data) in [
            str,
            bytes,
        ], "图片转 Data URLs 的参数 data 需要是全路径 str 或 bytes 数据"

        if isinstance(data, str):
            data_bytes = Path(data).read_bytes()
            data_base64_encoded = EncryptOperation.base64_encode(encode_data=data_bytes)

        else:
            data_base64_encoded = EncryptOperation.base64_encode(encode_data=data)
        return f"data:image/{mediatype};base64,{data_base64_encoded}"

    @staticmethod
    def gen_selenium_track(distance):
        """最简陋的根据缺口距离获取轨迹的方法，以供 selenium 使用

        Args:
            distance: 滑块缺口的距离

        Returns:
            tracks_dict:
                forward_tracks: 往右划的轨迹数组
                back_tracks: 回退（往左划）的轨迹数组
        """
        distance += 20
        v = 0
        t = 0.2
        forward_tracks = []
        current = 0
        mid = distance * 3 / 5
        while current < distance:
            a = 2 if current < mid else -3
            s = v * t + 0.5 * a * (t**2)
            v = v + a * t
            current += s
            forward_tracks.append(round(s))

        back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
        return {"forward_tracks": forward_tracks, "back_tracks": back_tracks}

    @staticmethod
    def gen_tracks(distance):
        """轨迹生成方法

        Args:
            distance: 滑块缺口的距离

        Returns:
            xyt: 轨迹数组
        """
        t_list = [random.randint(50, 160)]
        x_list = [random.randint(5, 11)]
        y_list = []
        # 生成x坐标轨迹, 生成t坐标轨迹
        for j in range(1, distance):
            x_list.append(x_list[j - 1] + random.randint(2, 4))
            if x_list[j] > distance:
                break

        diff = x_list[-1] - distance
        for j in range(diff):
            x_list.append(x_list[-1] + random.randint(-2, -1))
            if x_list[-1] <= distance:
                x_list[-1] = distance
                break

        length = len(x_list)
        # 生成y坐标轨迹
        for i in range(1, length + 1):
            if i < int(length * 0.4):
                y_list.append(0)
            elif i < int(length * 0.65):
                y_list.append(-1)
            elif i < int(length * 0.77):
                y_list.append(-2)
            elif i < int(length * 0.95):
                y_list.append(-3)
            else:
                y_list.append(-4)
            t_list.append(t_list[i - 1] + random.randint(20, 80))

        # 生成t的坐标
        xyt = list(zip(x_list, y_list, t_list))
        for j in range(length):
            xyt[j] = list(xyt[j])
        return xyt
