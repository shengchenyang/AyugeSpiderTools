#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  Encryption.py
@Time    :  2022/7/22 14:42
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import hashlib


__ALL__ = [
    'EncryptOperation',
]


class EncryptOperation(object):
    """
    普通加密方法
    """

    @classmethod
    def md5(cls, encrypt_data: str) -> str:
        """
        md5 处理方法
        Args:
            encrypt_data: 需要 md5 处理的参数

        Returns:
            1): md5 处理后的参数
        """
        hl = hashlib.md5()
        hl.update(encrypt_data.encode(encoding='utf-8'))
        return hl.hexdigest()
