#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_common_MultiPlexing.py
@Time    :  2022/8/19 13:33
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from ayugespidertools.common.MultiPlexing import ReuseOperation


def test_judge_str_is_json():
    data = '{"post_key1": "post_value1"}'
    res = ReuseOperation.judge_str_is_json(judge_str=data)
    print(res)
    data = 'post_key1=post_value1'
    res = ReuseOperation.judge_str_is_json(judge_str=data)
    print(res)
    assert res is not None


def test_get_items_except_keys():
    dict_config = {
        'alldata': {
            'article_detail_url': {
                'key_value': 'https://blog.csdn.net/weixin_52986315/article/details/126512431',
                'notes': '文章详情链接'},
            'article_title': {'key_value': '如何使用JavaMailSender给曾经心爱的她发送一封特别的邮件', 'notes': '文章标题'},
            'comment_count': {'key_value': '69', 'notes': '文章评论数量'}, 'favor_count': {'key_value': '41', 'notes': '文章赞成数量'},
            'nick_name': {'key_value': 'Binaire-沐辰', 'notes': '文章作者昵称'}
        },
        'table': 'article_info_list',
        'item_mode': 'Mysql'
    }
    res = ReuseOperation.get_items_except_keys(dict_config=dict_config, key_list=["table", "item_mode"])
    print("res:", res)
    assert res is not None


def test_get_ck_dict_from_headers():
    ck_str = "__gads=ID=5667bf1cc1623793-229892aad3d400f4:T=1656574796:RT=1656574796:S=ALNI_MYD2F7TGXOAaJFaIjtXL1pKiz8IwQ; _gid=GA1.2.1261442913.1661823137; _ga_5RS2C633VL=GS1.1.1661912227.10.0.1661912227.0.0.0; _ga=GA1.1.1076553851.1656574796; __gpi=UID=000007372209e6e0:T=1656574796:RT=1661912226:S=ALNI_MZkxoWl7cZYRkWzt2WKaxXQ7b47xw"

    res = ReuseOperation.get_ck_dict_from_headers(headers_ck_str=ck_str)
    print("ck_dict_res:", res, type(res))
    assert res is not None


def test_get_req_dict_from_scrapy():
    scrapy_body_str = "post_key1=post_value1&post_key2=post_value2"

    res = ReuseOperation.get_req_dict_from_scrapy(req_body_data_str=scrapy_body_str)
    print("req body dict:", res)
    assert res is not None


def test_extract_content():
    assert True
