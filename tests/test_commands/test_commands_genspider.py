#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_commands_genspider.py
@Time    :  2022/10/21 11:39
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.commands.genspider import AyuCommand


def test_genspider():
    AyuCommand().run(["demo_one", "csdn.net"], None)
    assert True
