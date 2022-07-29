#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  MongoClient.py
@Time    :  2022/7/22 15:43
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import pymongo
from gridfs import *
from typing import List, Dict
from pymongo import MongoClient
from urllib.parse import quote_plus


__ALL__ = [
    'MongoDbBase',
]


class MongoDbBase(object):
    """
    mongodb 数据库的相关操作（此功能暂时为残废状态，请参考 pymilk 库中的实现）
    """
    def __init__(self, user: str, pwd: str, host: str, port: int, database: str = None, connect_style: str = None):
        """
        初始化 mongo 连接句柄
        Args:
            user: 用户名
            pwd: 用户对应的密码
            host: mongoDB 链接需要的 host
            port: mongoDB 链接需要的端口
            database: mongoDB 链接需要的数据库
            connect_style: mongoDB 的链接方式，参数选择有：
                            1). uri: uri 方式；
                            2). key: 关键字变量方式；
                            3). auth: authenticate 或 admin 认证方式;
                            默认为 uri 方式
        """
        # uri 方式
        if any([not connect_style, connect_style in ["uri", "U"]]):
            uri = "mongodb://%s:%s@%s:%s" % (quote_plus(user), quote_plus(pwd), host, port)
            self.connect = MongoClient(uri)

        # 关键字变量方式
        elif connect_style in ["key", "K"]:
            self.connect = pymongo.MongoClient(host=host, port=port, username=user, password=pwd)

        # authenticate 或 admin 认证方式
        elif connect_style in ["auth", "A"]:
            self.connect = MongoClient(host, port)
            # 连接 admin 数据库，账号密码认证(其实这里也可以使用 uri 的 auth 认证方式)
            db = self.connect.admin
            db.authenticate(user, pwd)

        if database:
            self.db = self.init_db(database)

    def get_state(self):
        """
        获取 mongoDB 链接状态
        Returns:
            1). bool: 链接是否正常
        """
        return all([self.connect is not None, self.db is not None])

    def init_db(self, database: str):
        """
        指定链接的数据库为 database
        Args:
            database: 链接的目标数据库

        Returns:
            1). connect: 数据库链接
        """
        return self.connect[database]

    def insert_one(self, collection: str, data: dict) -> str:
        """
        插入一条数据
        Args:
            collection: 集合名称
            data: 插入的数据

        Returns:
            inserted_id: 成功返回的 id
        """
        if self.get_state():
            ret = self.db[collection].insert_one(data)
            return ret.inserted_id
        return ""

    def insert_many(self, collection: str, data: List[Dict]):
        """
        批量插入
        Args:
            collection: 集合名称
            data: 插入的数据数组

        Returns:
            inserted_ids: list: 成功返回的 ids
        """
        if self.get_state():
            ret = self.db[collection].insert_many(data)
            return ret.inserted_ids
        return ""

    def update(self, collection, data):
        """
        更新
        Args:
            collection: 集合名称
            data: 更新的数据

        Returns:
            modified_count: 更新影响的个数
        """
        # data format:
        # {key:[old_data,new_data]}
        data_filter = {}
        data_revised = {}
        for key in data.keys():
            data_filter[key] = data[key][0]
            data_revised[key] = data[key][1]
        if self.get_state():
            return self.db[collection].update_many(data_filter, {"$set": data_revised}).modified_count
        return 0

    def find(self, collection, condition, column=None):
        """
        查询
        Args:
            collection: 集合名称
            condition: 查询条件
            column:

        Returns:
            1). 查询条件的搜索结果
        """
        try:
            if self.get_state():
                if column is None:
                    return self.db[collection].find(condition)
                else:
                    return self.db[collection].find(condition, column)
            else:
                return None
        except Exception:
            return "查询数据格式有误"

    def t_update(self, collection, s_key, s_value, update_data):
        # self.db.get_collection(collection).update_one({s_key: s_value}, {"$set": update_data})
        return self.db[collection].update_one({s_key: s_value}, {"$set": {"groupProps": update_data}}).modified_count

    def update_normal(self, collection, s_key, s_value, data_style, update_data):
        return self.db[collection].update_one({s_key: s_value}, {"$set": {data_style: update_data}}).modified_count

    def update_super(self, collection: str, select_dict: dict, set_dict: dict):
        """
        更新
        Args:
            collection: 需要更新的集合
            select_dict: 更新的条件
            set_dict: 更新的内容

        Returns:
            1). modified_count: int: 更新影响的数量
        """
        return self.db[collection].update_one(select_dict, {"$set": set_dict}).modified_count

    # 删除
    def delete(self, collection, condition):
        if self.get_state():
            return self.db[collection].delete_many(filter=condition).deleted_count
        return 0

    # 上传数据
    def upLoadFile(self, file_name, collection, contentType, file_data, metadata):
        gridfs_col = GridFS(self.db, collection)
        # with open(file_name, 'rb') as file_r:
        #     file_data = file_r.read()
        #     file_ = gridfs_col.put(data=file_data, content_type=contentType, filename=file_name, metadata=metadata)
        #     # return file_

        file_ = gridfs_col.put(data=file_data, content_type=contentType, filename=file_name, metadata=metadata)
        return file_

    def getFileMd5(self, _id, collection):
        gridfs_col = GridFS(self.db, collection)
        gf = gridfs_col.get(_id)
        md5 = gf.md5
        _id = gf._id
        return {'_id': _id, 'md5': md5}

    def Upload(self, file_name, _id, contentType, collection, file_data):
        metadata = {
            "_contentType": contentType,
            "isThumb": 'true', "targetId": _id,
            "_class": "com.ccr.dc.admin.mongo.MongoFsMetaData"
        }

        gridfs_col = GridFS(self.db, collection)
        id = gridfs_col.put(data=file_data, content_type=contentType, filename=file_name, metadata=metadata)
        md5 = self.getFileMd5(id, 'fs')['md5']
        imageId = "/file/find/{}/{}".format(str(id), md5)
        return id, imageId

    def __del__(self):
        self.connect.close()
