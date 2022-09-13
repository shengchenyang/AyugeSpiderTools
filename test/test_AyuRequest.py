#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_AyuRequest.py
@Time    :  2022/8/30 16:17
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.AyuRequest import AiohttpRequest


def callback_tmp(response):
    print(response.text)


def test_aiohttp_reqeust():
    r = AiohttpRequest(
        url="https://www.baidu.com",
        callback=callback_tmp,
        method="GET",
        headers={
            "USER_AGENT": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36",
        },
        cookies={"name": "ayuge"},
        meta={
            "curr_page": 1,
        },
    )
    print(r)
    assert r is not None
