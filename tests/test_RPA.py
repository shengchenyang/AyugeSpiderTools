#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_RPA.py
@Time    :  2022/7/15 13:39
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.RPA import AboutPyppeteer


def test_deal_pyppeteer_suspend():
    # 暂时不测试此功能
    AboutPyppeteer.deal_pyppeteer_suspend(fn='logs/tmall.log', line=4)
    assert True
