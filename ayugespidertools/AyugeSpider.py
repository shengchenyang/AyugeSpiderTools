#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  AyugeSpider.py
@Time    :  2022/7/29 17:33
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import sys
import time
import threading
from typing import Union
from scrapy.spiders import Spider
from sqlalchemy import create_engine
from ayugespidertools.config import logger
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.common.MultiPlexing import ReuseOperation


__all__ = [
    "AyuSpider",
]


class MySqlEngineClass:
    """
    mysql 链接句柄单例模式
    """
    _instance_lock = threading.Lock()

    def __init__(self, engine_url):
        self.engine = create_engine(engine_url, pool_pre_ping=True, pool_recycle=3600 * 7)

    def __new__(cls, *args, **kwargs):
        if not hasattr(MySqlEngineClass, "_instance"):
            with cls._instance_lock:
                if not hasattr(MySqlEngineClass, "_instance"):
                    MySqlEngineClass._instance = object.__new__(cls)

        return MySqlEngineClass._instance


class AyuSpider(Spider):
    """
    用于初始配置 scrapy 的各种 setting 的值及 spider 全局变量等
    """
    # 自定义 common 设置
    custom_common_settings = {
        "ROBOTSTXT_OBEY": False,
        "TELNETCONSOLE_ENABLED": False,
        "RETRY_TIMES": 3,
        "DEPTH_PRIORITY": -1,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "ENV": "dev",
    }

    # 自定义 Debug 设置
    custom_debug_settings = {
        # 日志等级
        "LOG_LEVEL": "DEBUG",
        "ROBOTSTXT_OBEY": False,
        # 超时
        "DOWNLOAD_TIMEOUT": 20,
        # 重试次数
        "RETRY_TIMES": 3,
        # 禁用所有重定向
        "REDIRECT_ENABLED": False,
        # 后进先出，深度优先
        "DEPTH_PRIORITY": -1,
        # 环境
        "ENV": "test",
        # 数据库表枚举
        "DATA_ENUM": None,
        # 是否记录程序的采集情况基本信息到 Mysql 数据库
        "RECORD_LOG_TO_MYSQL": False,
    }

    # 自定义 product 设置
    custom_product_settings = {
        # 日志等级
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": False,
        # 超时
        "DOWNLOAD_TIMEOUT": 20,
        # 重试次数
        "RETRY_TIMES": 3,
        # 禁用所有重定向
        "REDIRECT_ENABLED": False,
        # 后进先出，深度优先
        "DEPTH_PRIORITY": -1,
        # 环境
        "ENV": "prod",
        # 数据库表枚举
        "DATA_ENUM": None,
        # 是否记录程序的采集情况基本信息到 Mysql 数据库
        "RECORD_LOG_TO_MYSQL": False,
    }

    # 开始采集时间
    SPIDER_TIME = time.strftime("%Y-%m-%d", time.localtime())
    # 是否启用 Debug 参数，默认激活 custom_common_settings
    settings_type = "common"
    # 脚本信息
    project_content = ""
    # 自定义数据库表枚举
    custom_table_enum = None
    # 数据库引擎开关
    mysql_engine_enabled = False

    def parse(self, response, **kwargs):
        """
        实现所继承类的 abstract 方法 parse
        """
        super(AyuSpider, self).parse(response, **kwargs)

    def __init__(self, *args, **kwargs):
        super(AyuSpider, self).__init__(*args, **kwargs)
        self.mysql_engine = None

    @classmethod
    def slog_init(cls, level: Union[str, list]) -> None:
        """
        日志全局配置

        can use it directly (e.g. Spider.slog.info('msg'))
        Almost the same as (spider.logger.info('msg'))
        loguru 文档中相关介绍:
            https://loguru.readthedocs.io/en/stable/resources/recipes.html#changing-the-level-of-an-existing-handler

        Args:
            level: loguru 等级配置参数
                1. 当参数为 str 时：设置日志等级只输出 level 之上
                2. 当参数为 list 时：设置日志输出列表中的级别

        Returns:
            None
        """
        assert type(level) in [str, list], "level 参数需要为 str 或 list 格式！"

        # 先删除其它所有的 handle，以防使用本库的其它项目中 loguru 日志配置相互影响
        logger.remove()
        if isinstance(level, str):
            logger.add(sys.stderr, level=level)
        else:
            logger.add(sys.stderr, filter=lambda record: record["level"].name in level)

    @classmethod
    def update_settings(cls, settings):
        custom_table_enum = getattr(cls, "custom_table_enum", None)
        # 设置类型，用于快速设置某些场景下的通用配置。比如测试 test 和生产 prod 下的通用配置；可不设置，默认为 common
        settings_type = getattr(cls, "settings_type", "common")
        # 根据 settings_type 参数取出对应的 inner_settings 配置
        inner_settings = getattr(cls, f"custom_{settings_type}_settings", {})

        if custom_table_enum:
            inner_settings["DATA_ENUM"] = custom_table_enum

        # 内置配置 inner_settings 优先级介于 project 和 spider 之间
        # 即优先级顺序：settings.py < inner_settings < custom_settings
        settings.setdict(inner_settings, priority="project")
        settings.setdict(cls.custom_settings or {}, priority="spider")

    @classmethod
    def get_mysql_config(cls, settings) -> Union[dict, None]:
        """
        根据环境获取相应的 Mysql 数据库配置，获取其他自定义配置
        Args:
            settings: crawler settings 配置信息

        Returns:
            1). Mysql 数据库链接配置
        """
        # 自定义 mysql 链接配置
        local_mysql_config = settings.get("LOCAL_MYSQL_CONFIG", {})
        # 是否开启应用配置管理
        app_conf_manage = settings.get("APP_CONF_MANAGE", False)
        # 优先从本地取配置，先判断是否配置两个中的任意一个
        if all([not local_mysql_config.get("DATABASE"), not app_conf_manage]):
            return None

        # 1). 从本地 local_mysql_config 的参数中取值
        if ReuseOperation.if_dict_meet_min_limit(
            dict_config=local_mysql_config,
            key_list=["HOST", "PORT", "USER", "PASSWORD", "CHARSET", "DATABASE"]
        ):
            mysql_conf_temp = {
                "host": local_mysql_config.get("HOST"),
                "port": local_mysql_config.get("PORT"),
                "user": local_mysql_config.get("USER"),
                "password": local_mysql_config.get("PASSWORD"),
                "database": local_mysql_config.get("DATABASE"),
                "charset": local_mysql_config.get("CHARSET") or "utf8mb4"
            }
            return mysql_conf_temp

        # 2). 本地没有配置，再从 consul 中获取应用配置
        if app_conf_manage:
            consul_conf_dict_min = ReuseOperation.get_consul_conf(settings=settings)
            return ToolsForAyu.get_mysql_conf_by_consul(**consul_conf_dict_min)

    @classmethod
    def get_mongodb_config(cls, settings) -> Union[dict, None]:
        """
        根据环境获取相应的 mongoDB 数据库配置，获取其他自定义配置
        Args:
            settings: crawler settings 配置信息

        Returns:
            1). MongoDB 数据库链接配置
        """
        # 自定义 mysql 链接配置
        local_mongodb_conf = settings.get("LOCAL_MONGODB_CONFIG", {})
        # 是否开启应用配置管理
        app_conf_manage = settings.get("APP_CONF_MANAGE", False)
        # 优先从本地取配置
        if all([not local_mongodb_conf.get("DATABASE"), not app_conf_manage]):
            return None

        # 1). 从本地 local_mongo_conf 的参数中取值
        if ReuseOperation.if_dict_meet_min_limit(
            dict_config=local_mongodb_conf,
            key_list=["HOST", "PORT", "USER", "PASSWORD", "DATABASE"]
        ):
            mongodb_conf_temp = {
                "host": local_mongodb_conf.get("HOST"),
                "port": local_mongodb_conf.get("PORT"),
                "user": local_mongodb_conf.get("USER"),
                "password": local_mongodb_conf.get("PASSWORD"),
                "database": local_mongodb_conf.get("DATABASE"),
            }
            return mongodb_conf_temp

        # 2). 本地没有配置，再从 consul 中获取应用配置
        if app_conf_manage:
            consul_conf_dict_min = ReuseOperation.get_consul_conf(settings=settings)
            return ToolsForAyu.get_mongodb_conf_by_consul(**consul_conf_dict_min)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AyuSpider, cls).from_crawler(crawler, *args, **kwargs)

        # 取出日志等级，同样配置给 loguru
        normal_logger_level = crawler.settings.get("LOG_LEVEL", "DEBUG")
        cls.slog_init(level=normal_logger_level)
        # 将 spider.slog 的日志功能替代为 spider.logger，具有同样功能
        spider.slog = logger
        # 先输出下相关日志，用于调试时查看
        spider.slog.debug(f"settings_type 配置: {cls.settings_type}")
        spider.slog.debug(f"scrapy 当前配置为: {dict(crawler.settings)}")

        # 1).先配置 Mysql 的相关信息，如果存在 Mysql 配置，则把 mysql_conf 添加到 spider 上
        mysql_conf = cls.get_mysql_config(crawler.settings)
        # 如果配置了 Mysql 信息
        if mysql_conf:
            spider.slog.info("项目中配置了 mysql_config 信息")
            spider.mysql_config = mysql_conf
            spider.stats = crawler.stats

            # 如果打开了 mysql_engine_enabled 参数(用于 spiders 中数据入库前去重查询)
            if cls.mysql_engine_enabled:
                mysql_url = "mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(
                    mysql_conf.get("user"),
                    mysql_conf.get("password"),
                    mysql_conf.get("host"),
                    mysql_conf.get("port"),
                    mysql_conf.get("database"),
                    mysql_conf.get("charset")
                )
                spider.mysql_engine = MySqlEngineClass(engine_url=mysql_url).engine

        # 2).配置 MongoDB 的相关信息，如果存在 MongoDB 配置，则把 mongodb_conf 添加到 spider 上
        mongodb_conf = cls.get_mongodb_config(crawler.settings)
        # 如果配置了 MongoDB 信息
        if mongodb_conf:
            spider.slog.info("项目中配置了 mongodb_config 信息")
            spider.mongodb_conf = mongodb_conf

        return spider
