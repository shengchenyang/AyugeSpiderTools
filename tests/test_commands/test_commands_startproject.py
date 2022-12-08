#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_commands_startproject.py
@Time    :  2022/10/21 11:28
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.commands.startproject import AyuCommand


def test_startproject():
    AyuCommand().run(["startproject", "DemoSpider"], None)
    assert True
