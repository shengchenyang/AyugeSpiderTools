#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_Encryption.py
@Time    :  2022/7/22 14:50
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.common.Encryption import EncryptOperation


def test_md5():
    md5_res = EncryptOperation.md5("123456")
    print(md5_res)
    assert md5_res == "e10adc3949ba59abbe56e057f20f883e"
