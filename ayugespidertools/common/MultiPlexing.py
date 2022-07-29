#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  MultiPlexing.py
@Time    :  2022/7/12 16:53
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import cv2
import numpy as np


__all__ = [
    'ReuseOperation',
]


class ReuseOperation(object):
    """
    用于存放经常复用的一些操作
    """

    @staticmethod
    def read_image_data(bg, tp):
        if any([type(bg) != str, type(bg) == bytes]):
            bg_buf = np.frombuffer(bg, np.uint8)
            tp_buf = np.frombuffer(tp, np.uint8)

            bg_cv = cv2.imdecode(bg_buf, cv2.IMREAD_ANYCOLOR)
            tp_cv = cv2.imdecode(tp_buf, cv2.IMREAD_ANYCOLOR)

        else:
            # 读取图片，读进来直接是 BGR 格式数据格式在 0~255
            bg_cv = cv2.imread(bg)
            # 0 表示采用黑白的方式读取图片
            tp_cv = cv2.imread(tp, 0)

        return bg_cv, tp_cv
