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
    sql_pre, sql_after = AboutSql.select_generate(db_table="zhihu_answer_info", key=["id", "q_title"], rule={"q_title|=": "我好好的跟女儿谈人际，就问了一个问题，她不说，就坐在床上有些嘲讽的笑，我说了半天也不回，有必要吗？"})
    status, res = mysql_client.search_data(sql_pre, sql_after, type="one")
    print("查询结果:", status, res)
    assert status == 1


def test_insert_data():
    insert_sql, insert_value = AboutSql.insert_generate(db_table="user", data={"name": "zhangsan", "age": 18})
    mysql_client.insert_data(insert_sql, insert_value)
    assert True


def test_update_data():
    update_sql, update_value = AboutSql.update_generate(db_table="user", data={"score": 4}, rule={"name": "zhangsan"})
    mysql_client.update_data(update_sql, update_value)
    assert True


sql_pre, sql_after = AboutSql.select_generate(db_table="zhihu_answer_info", key=["id", "q_title"], rule={"q_title|=": "我好好的跟女儿谈人际，就问了一个问题，她不说，就坐在床上有些嘲讽的笑，我说了半天也不回，有必要吗？"})
status, res = mysql_client.search_data(sql_pre, sql_after, type="one")
