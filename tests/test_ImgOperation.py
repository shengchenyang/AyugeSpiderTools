#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_ImgOperation.py
@Time    :  2022/7/12 16:59
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.ImgOperation import Picture


def test_identify_gap():
    # 参数为图片全路径的情况
    gap_distance = Picture.identify_gap("doc/image/2.jpg", "doc/image/1.png")
    print("滑块验证码的缺口距离1为：", gap_distance)
    assert gap_distance in list(range(205, 218))

    # 参数为图片 bytes 的情况
    with open("doc/image/1.png", "rb") as f:
        target_bytes = f.read()
    with open("doc/image/2.jpg", "rb") as f:
        template_bytes = f.read()
    gap_distance = Picture.identify_gap(template_bytes, target_bytes, "doc/image/33.png")
    print("滑块验证码的缺口距离2为：", gap_distance)
    assert gap_distance in list(range(205, 218))

