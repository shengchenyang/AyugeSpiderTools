#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_MysqlClient.py
@Time    :  2022/7/14 10:06
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools import MysqlClient
from ayugespidertools.config import NormalConfig
from ayugespidertools.common import SqlFormat


# mysql 连接
mysql_client = MysqlClient.MysqlOrm(NormalConfig.LOCAL_PYMYSQL_CONFIG)


def test_select_data():
    sql_pre, sql_after = SqlFormat.select_generate(db_table="newporj", key=["id", "title"], rule={"id|<=": 5})
    status, res = mysql_client.search_data(sql_pre, sql_after, type="one")
    print("查询结果:", status, res)
    assert status == 1, res == "美团终于上市了：市值超越小米和京东，仅次于 BAT"


def test_insert_data():
    insert_sql, insert_value = SqlFormat.insert_generate(db_table="user", data={"name": "zhangsan", "age": 18})
    mysql_client.insert_data(insert_sql, insert_value)
    assert True


def test_update_data():
    update_sql, update_value = SqlFormat.update_generate(db_table="user", data={"score": 4}, rule={"name": "zhangsan"})
    mysql_client.update_data(update_sql, update_value)
    assert True
