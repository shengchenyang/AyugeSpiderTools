#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_Items.py
@Time    :  2022/8/25 16:03
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from itemadapter import ItemAdapter
from ayugespidertools.Items import MysqlDataItem, ScrapyClassicItem, OldMongoDataItem


def test_items():
    m = MysqlDataItem()
    m.table = "test_table"
    m.alldata = {"test_all_data": "1"}
    print("mdi:", m, type(m))
    d_adapter = ItemAdapter(m)
    all_data = d_adapter.get("alldata")
    print("all data scrapy:", all_data, ItemAdapter.is_item(m), d_adapter["alldata"])

    s = ScrapyClassicItem()
    s["table"] = "s_table"
    s["alldata"] = {"s_all_data": 2}
    s["item_mode"] = "Mysql"
    print("s:", s, type(s))
    print("s dict:", dict(s))

    scrapy_adapter = ItemAdapter(s)
    all_data = scrapy_adapter.get("alldata")
    print("all data:", all_data, ItemAdapter.is_item(s))

    a = {
        "alldata": {"k": "v"},
        "table": "table_name",
        "item_mode": "Mysql",
    }
    my_dict_adapter = ItemAdapter(a)
    all_data = my_dict_adapter.get("alldata")
    print("my alldata:", all_data, ItemAdapter.is_item(a))
    assert m is not None


def test_old_item():
    omd = OldMongoDataItem()
    # omd.item_mode = "mongo"
    omd.table = "demo"
    print("ddd", dict(ItemAdapter(omd)))
    print(omd)
    a = dict()
    a.update(ItemAdapter(omd))
    print(a)

