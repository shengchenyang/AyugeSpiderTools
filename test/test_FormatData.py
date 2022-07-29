#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_mytools.py
@Time    :  2022/7/11 9:20
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools import FormatData


def test_get_full_url():
    full_url = FormatData.get_full_url(domain_name="https://static.geetest.com", deal_url="/captcha_v3/batch/v3/2021-04-27T15/word/4406ba6e71cd478aa31e0dca37601cd4.jpg")
    print(f"完整的链接 get_full_url 为: {full_url}")
    assert full_url


def test_click_point_deal():
    res = FormatData.click_point_deal(13.32596516, 3)
    print(f"小数点保留 3 位后的 click_point_deal 为: {res}")
    assert res


def test_normal_to_stamp():
    normal_stamp = FormatData.normal_to_stamp("Fri, 22 Jul 2022 01:43:06 +0800")
    print("normal_stamp:", normal_stamp)
    assert normal_stamp == 1658425386

    normal_stamp = FormatData.normal_to_stamp("Thu Jul 22 17:59:44 2022")
    print("normal_stamp2:", normal_stamp)
    assert normal_stamp == 1658483984

    normal_stamp = FormatData.normal_to_stamp("2022-06-21 16:40:00")
    print("normal_stamp3:", normal_stamp)

    normal_stamp = FormatData.normal_to_stamp("2022/06/21 16:40:00")
    print("normal_stamp4:", normal_stamp)

    # 当是英文的其他格式，或者混合格式时，需要自己自定时间格式化符
    normal_stamp = FormatData.normal_to_stamp("2022/Dec/21 16:40:00", "%Y/%b/%d %H:%M:%S")
    print("normal_stamp5:", normal_stamp)
