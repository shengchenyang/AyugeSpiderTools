#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  cofing.py
@Time    :  2022/7/12 11:22
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import os
import configparser
from environs import Env
from loguru import logger
from os.path import dirname, abspath, join


__all__ = [
    "NormalConfig",
]


env = Env()
env.read_env()


class NormalConfig(object):
    """
    用于存放此项目的通用配置
    """

    # 项目根目录
    CONFIG_DIR = dirname(abspath(__file__))
    ROOT_DIR = os.path.dirname(CONFIG_DIR)

    LOG_DIR = join(CONFIG_DIR, "logs")
    DOC_DIR = join(CONFIG_DIR, "doc")
    COMMON_DIR = join(CONFIG_DIR, "common")

    # 加载秘钥等配置信息
    config = configparser.ConfigParser()
    config.read("../../VIT/.conf", encoding="utf-8")

    # 加载 pypi 包 toml 的配置信息
    config.read(f"{ROOT_DIR}/pyproject.toml", encoding="utf-8")

    # 测试 Mysql 数据库配置信息，已脱敏，请自行配置后测试
    mysql_config = config["DEV_MYSQL"]
    mongodb_config = config["DEV_MONGODB"]
    oss_config = config["DEV_ALI_OSS"]

    LOCAL_PYMYSQL_CONFIG = {
        "host": mysql_config["HOST"],
        "port": mysql_config["PORT"],
        "user": mysql_config["USER"],
        "password": mysql_config["PWD"],
        "database": mysql_config["DATABASE"],
        "charset": mysql_config["CHARSET"],
        # "cursorclass": pymysql.cursors.Cursor,
    }

    # 测试 MongoDB 数据库配置信息，已脱敏，请自行配置后测试
    LOCAL_MONGODB_CONFIG = {
        "host": mongodb_config["HOST"],
        "port": mongodb_config["PORT"],
        "user": mongodb_config["DATABASE"],
        "pwd": mongodb_config["USER"],
        "database": mongodb_config["PWD"],
    }

    # 测试 MongoDB 数据库配置信息，已脱敏，请自行配置后测试
    LOCAL_MONGODB_CONN_URI = config["DEV_MONGODB_URI"]["CONN_URI"]

    # 读取 Pypi 包 toml 配置中的版本信息
    version = config["tool.poetry"]["version"]

    # 读取 Oss 配置信息，已脱敏，请自行配置后测试
    OSS_CONFIG = {
        "OssAccessKeyId": oss_config["OSSACCESSKEYID"],
        "OssAccessKeySecret": oss_config["OSSACCESSKEYSECRET"],
        "Endpoint": oss_config["ENDPOINT"],
        "examplebucket": oss_config["EXAMPLEBUCKET"],
        "operateDoc": oss_config["OPERATEDOC"],
    }


# 日志管理
logger.add(env.str("LOG_RUNTIME_FILE", f"{NormalConfig.LOG_DIR}/runtime.log"), level="DEBUG", rotation="1 week", retention="7 days")
logger.add(env.str("LOG_ERROR_FILE", f"{NormalConfig.LOG_DIR}/error.log"), level="ERROR", rotation="1 week", retention="7 days")


if __name__ == "__main__":
    print(NormalConfig.ROOT_DIR)
    print(NormalConfig.LOCAL_PYMYSQL_CONFIG)
    print(NormalConfig.version)
