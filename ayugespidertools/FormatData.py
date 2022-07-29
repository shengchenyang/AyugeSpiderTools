#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  format_data.py
@Time    :  2022/7/8 10:33
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import re
import time
import datetime
from urllib.parse import urljoin

__all__ = [
    'get_full_url',
    'click_point_deal',
    'judge_utc_time',
    'judge_include_letter',
    'normal_to_stamp',
]


def get_full_url(domain_name: str, deal_url: str) -> str:
    """
    根据域名 domain_name 拼接 deal_url 来获得完整链接
    Args:
        domain_name: 域名链接
        deal_url: 需要拼接的 url

    Returns:
        full_url: 拼接完整的链接
    """
    full_url = urljoin(domain_name, deal_url)
    return full_url


def click_point_deal(decimal: float, decimal_places=2) -> float:
    """
    将小数 decimal 保留小数点后 decimal_places 位，结果四舍五入
    Args:
        decimal: 需要处理的小数
        Decimal_places: 需要保留的小数点位数

    Returns:
        decimal(float): 四舍五入后的小数点
    """
    # 先拼接需要保留的位数
    decimal_deal = "%.{}f".format(decimal_places)
    return float(decimal_deal % float(decimal))


def judge_utc_time(local_time: str) -> bool:
    """
    判断 local_time 是否为 utc 格式的时间
    Args:
        local_time: 需要判断的时间参数，比如：Thu Jul 21 17:59:44 2022 或 Fri, 22 Jul 2022 01:43:06 +0800 等等

    Returns:
        1): 是否为 utc 格式的数据
    """
    pattern = re.compile(r"""mon|tues|wed|thu|fri|sat|sun""")
    res = pattern.findall(local_time.lower())
    if res:
        return True
    return False


def judge_include_letter(local_time: str) -> bool:
    pattern = re.compile(r"""[a-zA-Z]""")
    res = pattern.findall(local_time.lower())
    if res:
        return True
    return False


def _get_format_t(date_style: str = "", date_is_full: bool = False) -> str:
    """
    将需要格式化的数据用 date_style 标识来拼接起来，如果 date_is_full 为 True 时，则需要补齐"时分秒"位
    Args:
        date_style: 将格式化符拼接时需要的标识，比如：-
        date_is_full: 是否需要完整的时间格式化（即是否需要补齐"时分秒"单位）

    Returns:
        finally_t_format: 最终的格式化拼接结果，比如：%Y-%m-%d %H-%M-%S
    """
    # 年月日
    _y_m_d = ["%Y", "%m", "%d"]
    # 时分秒
    _h_m_s = ["%H", "%M", "%S"]

    _y_m_d_format = date_style.join(_y_m_d)
    # 时分秒大都为":"连接
    _h_m_s_format = ":".join(_h_m_s)

    if date_is_full:
        finally_t_format = " ".join([_y_m_d_format, _h_m_s_format])
        return finally_t_format
    return _y_m_d_format


def _time_format(date_str) -> str:
    """
    判断时间是什么格式的，比如：xxxx-xx-xx 或 xxxx.xx.xx
    Args:
        date_str: 需要判断格式的时间

    Returns:
        1): 时间格式的标识，比如：-
    """
    format_style_list = ['-', '.', '/', '年']
    for format_style in format_style_list:
        if format_style in date_str:
            return format_style
    return ""


def normal_to_stamp(normal_time: str, _format_t: str = None, date_is_full: bool = True) -> int:
    """
    将网页正常时间转为时间戳
    Args:
        normal_time: 需要转换的时间
        _format_t: 时间格式化符，默认不填。除非在英文时间的参数出错时可指定 _format_t 的值
        date_is_full: 是否包含"时分秒"单位的完整格式

    Returns:
        stamp: 返回的时间戳
    """
    # 判断 normal_time 是否是特殊模式
    is_utc_time = judge_utc_time(normal_time)
    is_letter_time = judge_include_letter(normal_time)
    # stamp = None
    if any([is_utc_time, is_letter_time]):
        # 如果不传递时间的格式符参数
        if not _format_t:
            if "," in normal_time:
                _format_t = "%a, %d %b %Y %H:%M:%S +0800"
            else:
                _format_t = "%a %b %d %H:%M:%S %Y"

        standard_time = datetime.datetime.strptime(normal_time, _format_t)
        stamp = time.mktime(time.strptime(str(standard_time), _get_format_t('-', True)))

    else:
        # 先判断正常时间的格式
        date_style = _time_format(normal_time)
        # standard_time_format = _get_format_t(date_style, date_is_full).replace('%m', '%b').replace('-', '/')
        standard_time_format = _get_format_t(date_style, date_is_full)
        print("qqqq", standard_time_format)
        stamp = time.mktime(time.strptime(normal_time, standard_time_format))

    return int(stamp)
