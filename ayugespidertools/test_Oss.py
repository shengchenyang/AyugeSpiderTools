#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_Oss.py
@Time    :  2022/7/22 15:03
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.Oss import AliOssBase
from ayugespidertools.config import NormalConfig


def test_put_oss():
    # TODO: 暂不测试，后续添加
    AliOssBase(**NormalConfig.OSS_CONFIG)
