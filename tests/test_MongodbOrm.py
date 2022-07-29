#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_mongodb.py
@Time    :  2022/7/25 17:41
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from pymongo import MongoClient
from ayugespidertools.config import NormalConfig
from ayugespidertools.MongodbOrm import mongo, mc


# mongoDB 链接配置信息
LOCAL_MONGODB_CONN_URI = NormalConfig.LOCAL_MONGODB_CONN_URI


def mkconn():
    """建立 mongo 链接"""
    return MongoClient(LOCAL_MONGODB_CONN_URI)


# 创建 mongo 连接
conn = mongo(mkconn=mkconn)
# 创建表对象(在添加数据时才会添加集合)
sheet = conn['test', 'test_sheet']


def test_insert():
    line1 = {'姓名': '小一', '年龄': 11, '幸运数字': [1, 2, 3, 4], '成绩': {'语文': 81, '数学': 82, '英语': 83}}
    line2 = {'姓名': '小二', '年龄': 12, '幸运数字': [2, 3, 4, 5], '成绩': {'语文': 82, '数学': 83, '英语': 84}}
    line3 = {'姓名': '小三', '年龄': 13, '幸运数字': [3, 4, 5, 6], '成绩': {'语文': 83, '数学': 84, '英语': 85}}
    line4 = {'姓名': '小四', '年龄': 14, '幸运数字': [4, 5, 6, 7], '成绩': {'语文': 84, '数学': 85, '英语': 86}}
    line5 = {'姓名': '小五', '年龄': 15, '幸运数字': [5, 6, 7, 8], '成绩': {'语文': 85, '数学': 86, '英语': 87}}
    line6 = {'姓名': '小六', '年龄': 16, '幸运数字': [6, 7, 8, 9], '成绩': {'语文': 86, '数学': 87, '英语': 88}}

    # 单条添加
    res = sheet + line1
    print(res, type(res))
    assert res is not None

    # 批量添加
    res = sheet + [line2, line3, line4, line5, line6]
    print("2222", res, type(res))
    print("insert 后的所有数据有：", sheet[:])
    assert len(res.inserted_ids) == 5


def test_select():
    # res = sheet[mc.年龄 >= 16][mc.成绩.语文 >= 86][:]
    res = sheet[mc.年龄 >= 16][mc.成绩.语文 >= 86][mc.幸运数字 == [6, 7, 8, 9]][:]
    print("11", res)
