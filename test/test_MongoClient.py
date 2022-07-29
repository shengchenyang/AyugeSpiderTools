#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  test_MongoClient.py
@Time    :  2022/7/25 11:21
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
from bson.objectid import ObjectId
from ayugespidertools.config import NormalConfig
from ayugespidertools.MongoClient import MongoDbBase


# mongoDB 链接配置信息
LOCAL_MONGODB_CONFIG = NormalConfig.LOCAL_MONGODB_CONFIG


def test_uri_connect():
    """测试 mongoDB 的 uri 链接方式"""
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    print(mongodb)
    assert mongodb is not None


def test_key_connect():
    """测试 mongoDB 的 key 关键字链接方式"""
    LOCAL_MONGODB_CONFIG['connect_style'] = "K"
    print(LOCAL_MONGODB_CONFIG)
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    print(mongodb)
    assert mongodb is not None


def test_auth_connect():
    """测试 mongoDB 的 auth 认证链接方式"""
    LOCAL_MONGODB_CONFIG['connect_style'] = "A"
    print(LOCAL_MONGODB_CONFIG)
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    print(mongodb)
    assert mongodb is not None


def test_insert_one():
    """测试 mongoDB 插入一条数据"""
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    insert_res = mongodb.insert_one("title", {"name": "标题名称", "addtime": "2020-07-25", "adduser": "mine"})
    print(insert_res, type(insert_res))
    assert insert_res is not None


def test_insert_many():
    """测试 mongoDB 插入一条数据"""
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    insert_res = mongodb.insert_many("title", [{"name": "标题名称3", "addtime": "2020-07-25", "adduser": "mine3"}, {"name": "标题名称2", "addtime": "2020-07-25", "adduser": "mine2"}])
    print(insert_res, type(insert_res))
    assert insert_res is not None


def test_update():
    """测试 mongoDB 更新数据"""
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    update_res = mongodb.update_super(collection="title", select_dict={'name': '标题名称32'}, set_dict={'name': '标题名称3'})
    print("update_res:", update_res)
    assert update_res is not None


def test_delete():
    """测试 mongoDB 删除数据"""
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    delete_res = mongodb.delete('title', {'name': {'$regex': '标题名称3'}})
    print("delete_res:", delete_res)
    assert delete_res is not None


def test_find():
    """测试 mongoDB 查询数据"""
    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    select_res = mongodb.find('title', {'name': '标题名称3'}).count()
    print("select_res:", select_res)
    select_res = list(mongodb.find("title", {'name': {'$exists': True}}, {'name': 1, 'addtime': 1, '_id': 0}).limit(5).skip(2))
    print("select_res:", select_res)
    select_res = list(mongodb.find('title', {'_id': ObjectId('62de112a907ce5580321e1bd')}, {'_id': 1, 'name': 1}))
    print("select_res:", select_res)
    assert 1


def test_upload():
    """测试 mongoDB 上传图片方法"""
    import requests

    mongodb = MongoDbBase(**LOCAL_MONGODB_CONFIG)
    r = requests.get(url="https://static.geetest.com/captcha_v3/batch/v3/6677/2022-07-25T15/word/20a22d16da794a3ca5078a4286280c07.jpg?challenge=1aac413494d047963704a762e5635f85")
    content_type = dict(r.headers)['Content-Type']
    print("ccccc", content_type)
    # 返回上传后的 ID 及图片链接
    id, image_id = mongodb.Upload(file_name="aaa.jpg",  _id="121212121212", contentType=content_type, collection="fs", file_data=r.content)
    print(id, image_id)
