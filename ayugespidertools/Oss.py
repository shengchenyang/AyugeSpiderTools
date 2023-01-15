#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  Oss.py
@Time    :  2022/7/22 13:44
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  阿里云 Oss 对象存储 python sdk 示例
    其 GitHub 官方文档地址：
        https://github.com/aliyun/aliyun-oss-python-sdk?spm=5176.8465980.tools.dpython-github.572b1450ON6Z9R
    阿里云官方 oss sdk 文档地址：
        https://www.alibabacloud.com/help/zh/object-storage-service/latest/python-quick-start
"""
import oss2
import requests
from typing import Union
from retrying import retry
from ayugespidertools.common.Params import Param
from ayugespidertools.common.Encryption import EncryptOperation
# 去除 requests 的警告信息
import warnings
warnings.filterwarnings('ignore')


__all__ = [
    'AliOssBase',
]


class AliOssBase(object):
    """
    ali oss 所需要的基本方法
    """
    def __init__(
        self,
        OssAccessKeyId: str,
        OssAccessKeySecret: str,
        Endpoint: str,
        examplebucket: str,
        operateDoc: str
    ) -> None:
        """
        初始化 auth，bucket 等信息
        注：阿里云账号 AccessKey 拥有所有 API 的访问权限，风险很高；
            强烈建议您创建并使用 RAM 用户进行 API 访问或日常运维，请登录 RAM 控制台创建 RAM 用户
        Args:
            OssAccessKeyId: 阿里云账号 AccessKey
            OssAccessKeySecret: 阿里云账号 AccessKey 对应的秘钥
            Endpoint: 填写 Bucket 所在地域对应的 Endpoint；
                以华东1（杭州）为例，Endpoint 填写为 https://oss-cn-hangzhou.aliyuncs.com（注意二级域名等问题）
            examplebucket: 填写 Bucket 名称，此 oss 项目所在文件夹目录
        """
        self.Endpoint = Endpoint
        self.operateDoc = operateDoc
        self.examplebucket = examplebucket
        self.auth = oss2.Auth(OssAccessKeyId, OssAccessKeySecret)
        self.bucket = oss2.Bucket(self.auth, f'{self.Endpoint}/', self.examplebucket)
        self.headers = {'Connection': 'close'}

    def delete_oss(self, del_logo_url: str):
        """
        删除单个文件: 以下代码用于删除 examplebucket 中的 del_logo_url 所对应的文件
        Args:
            del_logo_url: 需要参数的阿里云链接全路径 url

        Returns:
            None
        """
        try:
            self.bucket.delete_object(
                f"{self.operateDoc}/{del_logo_url.replace(f'{self.Endpoint}/{self.operateDoc}/', '')}"
            )
        except oss2.exceptions.NoSuchKey as e:
            raise ValueError(
                'delete_oss error: status={0}, request_id={1}'.format(
                    e.status, e.request_id
                )
            ) from e

    @retry(stop_max_attempt_number=Param.retry_num, retry_on_result=lambda x: x[0] is False)
    def put_oss(
        self,
        put_bytes_or_url: Union[str, bytes],
        file_name: str,
        file_format: str,
        file_name_md5: bool = False
    ) -> (bool, str):
        """
        上传单个文件的 bytes 内容
        Args:
            put_bytes_or_url: 需要上传的文件 bytes 内容或链接
            file_name: 需要上传的文件的名称
            file_format: 需要上传的文件格式，比如：jpg, png, wav 等
            file_name_md5: 文件名称是否需要 md5 处理

        Returns:
            1): 上传状态，是否成功
            2): 上传成功至 Oss 的目标 url
        """
        assert type(put_bytes_or_url) in [str, bytes], "参数：上传的文件需要是 str 或 bytes 格式"

        input_file_name = EncryptOperation.md5(file_name) if file_name_md5 else file_name
        if isinstance(put_bytes_or_url, str):
            put_bytes_or_url = requests.get(url=put_bytes_or_url, headers=self.headers, verify=False).content

        try:
            self.bucket.put_object(
                f'{self.operateDoc}/{input_file_name}.{file_format}',
                put_bytes_or_url,
            )
        except Exception as e:
            return False, ''
        return True, input_file_name

    def enumer_file_by_pre(
        self,
        prefix: str,
        count_by_type: Union[Param.Str_Lstr, Param.NoneType] = None
    ) -> list:
        """
        列举 prefix 文件夹下的所有的 count_by_type 类型的文件元素
        Args:
            prefix: 文件夹目录
            count_by_type: 统计的依据，计数文件夹中的此类型的元素
                参数示例如下:
                    1. amr
                    2. ["amr", "mp3", "m4a", "wav", "aac", "ogg", "flac", "wma"]

        Returns:
            1). prefix 目录下的符合规则的文件列表
        """
        assert type(count_by_type) in [str, list, Param.NoneType], "计数依据的参数类型需要是 str 或 list"

        # 如果依据为空，则统计目标目录下的所有文件
        obj_list = list(oss2.ObjectIterator(self.bucket, prefix=prefix))
        if not count_by_type:
            return [obj.key for obj in obj_list][1:]

        # 返回符合单个约束的元素集
        if isinstance(count_by_type, str):
            return [obj.key for obj in obj_list if str(obj.key).endswith(count_by_type)]

        key_list = []
        for count_by in count_by_type:
            res = [obj.key for obj in obj_list if str(obj.key).endswith(count_by)]
            key_list = key_list + res
        return key_list
