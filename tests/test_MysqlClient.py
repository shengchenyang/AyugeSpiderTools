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
from ayugespidertools.common.SqlFormat import AboutSql


# mysql 连接
mysql_client = MysqlClient.MysqlOrm(NormalConfig.PYMYSQL_CONFIG)


def test_select_data():
    select_sql, select_value = AboutSql.select_generate(
        db_table="zhihu_answer_info",
        key=["id", "q_title"],
        rule={"q_id|=": "34987206"},
        limit=1
    )
    print(f"select_sql: {select_sql}, select_value: {select_value}")
    status, res = mysql_client.search_data(select_sql, select_value, type="one")
    print(f"status: {status}, res: {res}")
    assert status == 1


def test_insert_data():
    insert_sql, insert_value = AboutSql.insert_generate(db_table="user", data={"name": "zhangsan", "age": 18})
    print(f"insert_sql: {insert_sql}, insert_value: {insert_value}")
    mysql_client.insert_data(insert_sql, insert_value)
    assert True


def test_update_data():
    update_sql, update_value = AboutSql.update_generate(db_table="user", data={"score": 4}, rule={"name": "zhangsan"})
    print(f"update_sql: {update_sql}, update_value: {update_value}")
    mysql_client.update_data(update_sql, update_value)
    assert True
