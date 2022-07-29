#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  Oss.py
@Time    :  2022/7/22 13:44
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import oss2
import requests
from retrying import retry
from ayugespidertools.common.Encryption import EncryptOperation
# 去除 requests 的警告信息
import warnings
warnings.filterwarnings('ignore')


__ALL__ = [
    'AliOssBase',
]


def get_true_img_url(img_url: str) -> str:
    """
    获取真是的图片链接，去除链接中 x-bce-process 及以后的参数
    Args:
        img_url: 待处理的图片链接

    Returns:
        true_img_url: 去除链接中 x-bce-process 及以后的图片链接
    """
    true_img_url = img_url.split('?x-bce-process')[0]
    return true_img_url


class AliOssBase(object):
    """
    oss 所需要的基本方法
    """
    def __init__(self, OssAccessKeyId, OssAccessKeySecret, Endpoint, examplebucket, operateDoc):
        """
        初始化 auth，bucket 等信息
        注：阿里云账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM用户进行API访问或日常运维，请登录RAM控制台创建RAM用户
        Args:
            OssAccessKeyId: 阿里云账号 AccessKey
            OssAccessKeySecret: 阿里云账号 AccessKey 对应的秘钥
            Endpoint: 填写 Bucket 所在地域对应的Endpoint。以华东1（杭州）为例，Endpoint 填写为 https://oss-cn-hangzhou.aliyuncs.com（注意二级域名等问题）
            examplebucket: 填写 Bucket 名称
        """
        self.Endpoint = Endpoint
        self.operateDoc = operateDoc
        self.examplebucket = examplebucket
        self.auth = oss2.Auth(OssAccessKeyId, OssAccessKeySecret)
        self.bucket = oss2.Bucket(self.auth, '{}/'.format(self.Endpoint), self.examplebucket)
        self.headers = {'Connection': 'close', }

    def delete_oss(self, del_logo_url: str):
        """
        删除单个文件: 以下代码用于删除 examplebucket 中的 exampleobject.txt 文件
        Args:
            del_logo_url: 需要参数的阿里云链接全路径 url

        Returns:
            None
        """
        try:
            self.bucket.delete_object('{}/{}'.format(self.operateDoc, del_logo_url.replace('{}/{}/'.format(self.Endpoint, self.operateDoc), '')))
        except oss2.exceptions.NoSuchKey as e:
            raise Exception('delete_oss error: status={0}, request_id={1}'.format(e.status, e.request_id))

    def old_logo_status(self, old_logo_url: str) -> bool:
        """
        判断 old_logo_url 是否可访问
        Args:
            old_logo_url: 需要判断的链接参数

        Returns:
            1): 链接是否有效
        """
        r = requests.get(old_logo_url, headers=self.headers, verify=False)
        if r.status_code == 200:
            return True
        return False

    @retry(stop_max_attempt_number=3, retry_on_result=lambda x: x[0] is False)
    def put_oss(self, put_bytes_or_url: str, file_name, file_format: str, file_name_md5: bool = False) -> (bool, str):
        """
        上传单个文件的 bytes 内容
        Args:
            file_format: 需要上传的文件格式，比如：jpg, png, wav 等
            put_bytes_or_url: 需要上传的文件 bytes 内容或链接
            file_name: 需要上传的文件的名称
            file_name_md5: 文件名称是否需要 md5 处理

        Returns:
            1): 上传状态，是否成功
            2): 上传成功至 Oss 的目标 url
        """
        input_file_name = EncryptOperation.md5(file_name) if file_name_md5 else file_name
        if all([put_bytes_or_url.startswith("http"), type(put_bytes_or_url) != bytes]):
            put_bytes_or_url = requests.get(url=put_bytes_or_url, headers=self.headers, verify=False).content

        try:
            self.bucket.put_object('{}/{}.{}'.format(self.operateDoc, input_file_name, file_format), put_bytes_or_url)
        except Exception as e:
            return False, ''
        return True, input_file_name

    def get_file_style(self, media_par: str) -> str:
        """
        判断新增图片的格式类型（此方法是为了防止图片地址格式不统一，造成图片格式提取错误）
        Args:
            media_par: 需要判断格式类型的文件链接

        Returns:
            1): 文件的格式信息
        """
        image_style = ['.svg', '.png', '.jpg', '.jpeg', '.bmp', '.wav', '.mp3']
        for image_format in image_style:
            if image_format in media_par:
                return image_format[1:]
        raise Exception("未获取到文件的格式信息，请及时查看")

