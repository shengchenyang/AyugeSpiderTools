#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_VerificationCode.py
@Time    :  2022/7/11 14:18
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools import VerificationCode


def test_match_img_get_distance():
    distance_res = VerificationCode.match_img_get_distance("docs/image/new_target.jpg", "docs/image/new_template.png")
    print(f"滑块缺口位置1: {distance_res}")

    with open("docs/image/new_target.jpg", "rb") as f:
        target_bytes = f.read()
    with open("docs/image/new_template.png", "rb") as f:
        template_bytes = f.read()
    distance_res = VerificationCode.match_img_get_distance(target_bytes, template_bytes)
    print(f"滑块缺口位置2： {distance_res}")
    assert distance_res in list(range(195, 210))


def test_get_selenium_tracks():
    tracks = VerificationCode.get_selenium_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_yidun_tracks():
    tracks = VerificationCode.get_yidun_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_normal_track():
    tracks = VerificationCode.get_normal_track(space=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_yidun_gap():
    # 参数为图片全路径的情况
    tracks = VerificationCode.get_yidun_gap("docs/image/1.png", "docs/image/2.jpg", "docs/image/3.png")
    print("易盾滑块缺口距离 1 为：", tracks)
    assert tracks == 214

    # 参数为图片 bytes 的情况
    with open("docs/image/1.png", "rb") as f:
        target_bytes = f.read()
    with open("docs/image/2.jpg", "rb") as f:
        template_bytes = f.read()
    tracks = VerificationCode.get_yidun_gap(target_bytes, template_bytes, "docs/image/33.png")
    print("易盾滑块缺口距离 2 为：", tracks)
    assert tracks
