import datetime
import re
import time
from typing import Optional, Union
from urllib.parse import urljoin

import html2text
from w3lib.html import remove_tags, replace_entities

__all__ = [
    "DataHandle",
]


class DataHandle:
    """数据处理相关方法"""

    @staticmethod
    def get_full_url(domain_name: str, deal_url: str) -> str:
        """根据域名 domain_name 拼接 deal_url 来获得完整链接

        Args:
            domain_name: 域名链接
            deal_url: 需要拼接的 url

        Returns:
            1). 拼接完整的链接
        """
        return urljoin(domain_name, deal_url)

    @staticmethod
    def click_point_deal(decimal: float, decimal_places: int = 2) -> float:
        """将小数 decimal 保留小数点后 decimal_places 位，结果四舍五入

        Args:
            decimal: 需要处理的小数
            decimal_places: 需要保留的小数点位数

        Returns:
            decimal(float): 四舍五入后的小数点
        """
        # 先拼接需要保留的位数
        decimal_deal = f"%.{decimal_places}f"
        return float(decimal_deal % decimal)

    @staticmethod
    def judge_utc_time(local_time: str) -> bool:
        """判断 local_time 是否为 utc 格式的时间

        Args:
            local_time: 需要判断的时间参数，比如：Thu Jul 21 17:59:44 2022 或 Fri, 22 Jul 2022 01:43:06 +0800 等等

        Returns:
            1): 是否为 utc 格式的数据
        """
        pattern = re.compile(r"""mon|tues|wed|thu|fri|sat|sun""")
        return bool(pattern.findall(local_time.lower()))

    @staticmethod
    def judge_include_letter(local_time: str) -> bool:
        pattern = re.compile(r"""[a-zA-Z]""")
        return bool(pattern.findall(local_time.lower()))

    @staticmethod
    def _get_format_t(
        date_style: str = "",
        date_is_full: bool = False,
        specific_date_conn: str = " ",
        hms_conn: str = ":",
    ) -> str:
        """将需要格式化的数据用 date_style 标识来拼接起来，如果 date_is_full 为 True 时，则需要补齐"时分秒"位

        Args:
            date_style: 将格式化符拼接时需要的标识，比如：-
            date_is_full: 是否需要完整的时间格式化（即是否需要补齐"时分秒"单位）
            specific_date_conn: 年月日与时分秒拼接的方式
            hms_conn: 时分秒拼接的方式

        Returns:
            1). 最终的格式化拼接结果，比如：%Y-%m-%d %H-%M-%S
        """
        # 年月日
        _y_m_d = ["%Y", "%m", "%d"]
        _y_m_d_format = date_style.join(_y_m_d)

        if date_is_full:
            # 时分秒
            _h_m_s = ["%H", "%M", "%S"]
            # 时分秒大都为":"连接
            _h_m_s_format = hms_conn.join(_h_m_s)
            return specific_date_conn.join([_y_m_d_format, _h_m_s_format])
        return _y_m_d_format

    @staticmethod
    def _time_format(date_str) -> str:
        """判断时间是什么格式的，比如：xxxx-xx-xx 或 xxxx.xx.xx

        Args:
            date_str: 需要判断格式的时间

        Returns:
            1). 时间格式的标识，比如：-，若没有就返回空字符
        """
        format_styles = ["-", ".", "/", "年"]
        return next(
            (
                format_style
                for format_style in format_styles
                if format_style in date_str
            ),
            "",
        )

    @classmethod
    def normal_to_stamp(
        cls,
        normal_time: str,
        _format_t: Optional[str] = None,
        date_is_full: bool = True,
        specific_date_conn: str = " ",
        hms_conn: str = ":",
    ) -> int:
        """将网页正常时间转为时间戳

        Args:
            normal_time: 需要转换的时间
            _format_t: 时间格式化符，默认不填。除非在英文时间的参数出错时可指定 _format_t 的值
            date_is_full: 是否包含"时分秒"单位的完整格式
            specific_date_conn: 年月日与时分秒拼接的方式
            hms_conn: 时分秒拼接的方式

        Returns:
            stamp: 返回的时间戳
        """
        # 判断 normal_time 是否是特殊模式
        is_utc_time = cls.judge_utc_time(normal_time)
        is_letter_time = cls.judge_include_letter(normal_time)
        # stamp = None
        if any([is_utc_time, is_letter_time]):
            # 如果不传递时间的格式符参数
            if not _format_t:
                if "," in normal_time:
                    _format_t = "%a, %d %b %Y %H:%M:%S +0800"
                else:
                    _format_t = "%a %b %d %H:%M:%S %Y"
            standard_time = datetime.datetime.strptime(normal_time, _format_t)
            stamp = time.mktime(
                time.strptime(str(standard_time), cls._get_format_t("-", True))
            )

        else:
            # 先判断正常时间的格式
            date_style = cls._time_format(normal_time)
            # standard_time_format = _get_format_t(date_style, date_is_full).replace('%m', '%b').replace('-', '/')
            standard_time_format = cls._get_format_t(
                date_style, date_is_full, specific_date_conn, hms_conn
            )
            stamp = time.mktime(time.strptime(normal_time, standard_time_format))
        return int(stamp)

    @staticmethod
    def timestamp_to_normal(timestamp: Union[int, str]) -> str:
        """将时间戳转为正常时间 xxxx-xx-xx xx:xx:xx 的格式

        Args:
            timestamp: 需要处理的时间格式

        Returns:
            1). 转换后的时间结果
        """
        _timestamp = str(timestamp) if isinstance(timestamp, int) else timestamp
        timestamp_normal = int(_timestamp[:10])
        time_array = time.localtime(timestamp_normal)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    @staticmethod
    def remove_all_tags(func):
        """去除所有标签"""

        def inner(*args, **kwargs):
            func_res = func(*args, **kwargs)
            func_res = remove_tags(func_res)
            return func_res

        return inner

    @staticmethod
    def normal_display(func):
        """去除掉网页的注释(将网页中的特殊字符的源码改成正常显示)"""

        def inner(*args, **kwargs):
            func_res = func(*args, **kwargs)
            func_res = replace_entities(func_res)
            return func_res

        return inner

    @staticmethod
    def simple_deal_for_extract(func):
        """将 xpath, css 或 json 提取的数据做简单处理；提取的数据若非数组数据，则统一返回字符类型"""

        def inner(*args, **kwargs):
            func_res = func(*args, **kwargs)
            if type(func_res) in [str, int, float, bool]:
                # 这里可添加一些通用的数据处理
                return str(func_res).strip()
            else:
                return func_res

        return inner

    @classmethod
    def _extract_table_rule(
        cls, html_txt: str, h_obj: Optional[html2text.HTML2Text] = None
    ):
        """根据 html2text 来处理 html 中的 table 表格内容

        Args:
            html_txt: 网页内容
            h_obj: html2text 对象句柄

        Returns:
            1). 转换后的结果
        """
        if not h_obj:
            h_obj = html2text.HTML2Text()

        h_obj.protect_links = True
        h_obj.body_width = 0
        h_obj.ignore_links = True
        h_obj.bypass_tables = False
        return h_obj.handle(html_txt)

    @classmethod
    def extract_html_to_md(
        cls, html_txt: str, h_obj: Optional[html2text.HTML2Text] = None
    ) -> str:
        """将 html 内容转化为 markdown 内容
        更多、更详细的配置参数请查看文档内容: https://github.com/Alir3z4/html2text/blob/master/html2text/cli.py

        Args:
            html_txt: 网页内容（一般是带标签的内容）
            h_obj: html2text 对象句柄

        Returns:
            1). 转换后的结果
        """
        if not h_obj:
            h_obj = html2text.HTML2Text()

        # 以下步骤先处理通用部分，先不处理 table 内容
        h_obj.body_width = 0
        # h_obj.protect_links = True
        h_obj.bypass_tables = True
        # h_obj.unicode_snob = True
        h_obj.ignore_links = True
        content = h_obj.handle(html_txt)

        # 先处理表格 <table> 标签中格式
        table_pattern = re.compile(r"(<table.*?</table>)", flags=re.S)
        if table_res_list := table_pattern.findall(content):
            for table_res in table_res_list:
                table_deal = cls._extract_table_rule(html_txt=table_res, h_obj=h_obj)
                # 将 table 转换时去除多余的换行和空白字符等内容
                table_deal = re.sub(r"\|\s*\n", "| ", table_deal, flags=re.S)
                table_deal = re.sub(r"\n\s*\|", "| ", table_deal, flags=re.S)
                table_deal = re.sub(r"\n\s*\n", "\n\n", table_deal, flags=re.S)
                table_deal = re.sub(r"\r\n", "\n", table_deal, flags=re.S)
                table_deal = re.sub(r"[\n]{1,}", "\n", table_deal, flags=re.S)

                content = re.sub(
                    r"(<table.*?</table>)", table_deal + "\n", content, 1, re.S
                )

        # TODO: 可以添加上通用处理的装饰器
        # 将三个以上换行改为两个换行
        content = re.sub(r"[\n]{3,}", "\n\n", content)
        content = content.strip()
        return content
