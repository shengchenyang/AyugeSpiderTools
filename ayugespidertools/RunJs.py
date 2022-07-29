#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  RunJs.py
@Time    :  2022/7/8 14:55
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import execjs


__all__ = [
    'exec_js',
]


def exec_js(js_handle, method, *args):
    """
    执行 js_full_path 的 js 文件中的 method 方法
    Args:
        js_handle: js 处理对象，可能是 js_full_path 的全路径，也可能是 js 的 ctx 句柄
        method: 需要调用的 js 方法名
        *args: 调用的目标函数所需要的参数

    Returns:
        js_res: js 执行后的结果
    """
    # 先判断是否有 ctx 对象，如果有的话，直接调用 ctx 的方法即可，不用重复构造 ctx 对象
    if any([type(js_handle) != str, type(js_handle) == execjs._external_runtime.ExternalRuntime.Context]):
        js_res = js_handle.call(method, *args)

    # 没有 ctx 句柄则需要创建此对象
    else:
        with open(js_handle, 'r', encoding='utf-8') as f:
            js_content = f.read()
        ctx = execjs.compile(js_content)
        js_res = ctx.call(method, *args)
    return js_res
