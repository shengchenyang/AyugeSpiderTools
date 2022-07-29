#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_RunJs.py
@Time    :  2022/7/11 11:51
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools import RunJs
import execjs


def test_exec_js_by_file():
    """
    测试运行 ctx 句柄中的方法
    Returns:
        None
    """
    # 测试运行 js 文件中的方法
    js_res = RunJs.exec_js("doc/js/add.js", "add", 1, 2)
    print("test_exec_js:", js_res)
    assert js_res

    # 测试运行 ctx 句柄中的方法
    with open('doc/js/add.js', 'r', encoding='utf-8') as f:
        js_content = f.read()
    ctx = execjs.compile(js_content)

    js_res = RunJs.exec_js(ctx, "add", 1, 2)
    print("test_exec_js_by_file:", js_res)
    assert js_res
