#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_SqlFormat.py
@Time    :  2022/7/13 11:33
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.common import SqlFormat


def test_select_generate():
    select_sql, select_value = SqlFormat.select_generate(db_table="student", key=["id"], rule={"age|=": 18, "sex|!=": "male"})
    print("select_sql:", select_sql)
    print("select_value:", select_value)
    assert select_sql, select_value


def test_insert_generate():
    insert_sql, insert_value = SqlFormat.insert_generate(db_table="student", data={"name": "zhangsan", "age": 18})
    print("insert_sql:", insert_sql)
    print("insert_value:", insert_value)
    assert insert_sql, insert_value


def test_update_generate():
    update_sql, update_value = SqlFormat.update_generate(db_table="student", data={"score": 4}, rule={"name": "zhangsan"})
    print("update_sql:", update_sql)
    print("update_value:", update_value)
    assert update_sql, update_value
