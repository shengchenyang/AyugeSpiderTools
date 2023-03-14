import threading
import time
from typing import Union

from scrapy.spiders import Spider
from sqlalchemy import create_engine

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.config import logger

__all__ = [
    "AyuSpider",
]


class MySqlEngineClass:
    """
    mysql 链接句柄单例模式
    """

    _instance_lock = threading.Lock()

    def __init__(self, engine_url):
        self.engine = create_engine(
            engine_url, pool_pre_ping=True, pool_recycle=3600 * 7
        )

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
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 20,
        "RETRY_TIMES": 3,
        "REDIRECT_ENABLED": False,
        "DEPTH_PRIORITY": -1,
        "ENV": "prod",
        "DATA_ENUM": None,
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

    @property
    def slog(self):
        """
        本库的日志管理模块，使用 loguru 来管理日志；
        本配置可与 Scrapy 的 spider.log 同时管理，根据场景可以自行配置。
        """
        # 设置 loguru 日志配置
        loguru_config_tmp = self.crawler.settings.get("LOGURU_CONFIG")
        # 是否开启 loguru 日志记录
        loguru_enabled = self.crawler.settings.get("LOGURU_ENABLED", True)
        assert isinstance(loguru_enabled, bool), "loguru_enabled 参数格式需要为 bool"

        # 如果开启推荐的 loguru 日志管理功能
        if loguru_enabled:
            # 则使用 LOGURU_CONFIG 下的配置，或直接使用统一管理的 logger
            return loguru_config_tmp or logger

        # 如果关闭推荐的日志管理，则替换为 scrapy 的日志管理
        else:
            return super(AyuSpider, self).logger

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
        if ReuseOperation.is_dict_meet_min_limit(
            dict_config=local_mysql_config,
            key_list=["HOST", "PORT", "USER", "PASSWORD", "CHARSET", "DATABASE"],
        ):
            return {
                "host": local_mysql_config.get("HOST"),
                "port": local_mysql_config.get("PORT"),
                "user": local_mysql_config.get("USER"),
                "password": local_mysql_config.get("PASSWORD"),
                "database": local_mysql_config.get("DATABASE"),
                "charset": local_mysql_config.get("CHARSET") or "utf8mb4",
            }
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
        if ReuseOperation.is_dict_meet_min_limit(
            dict_config=local_mongodb_conf,
            key_list=["HOST", "PORT", "USER", "PASSWORD", "DATABASE"],
        ):
            return {
                "host": local_mongodb_conf.get("HOST"),
                "port": local_mongodb_conf.get("PORT"),
                "user": local_mongodb_conf.get("USER"),
                "password": local_mongodb_conf.get("PASSWORD"),
                "database": local_mongodb_conf.get("DATABASE"),
            }
        # 2). 本地没有配置，再从 consul 中获取应用配置
        if app_conf_manage:
            consul_conf_dict_min = ReuseOperation.get_consul_conf(settings=settings)
            return ToolsForAyu.get_mongodb_conf_by_consul(**consul_conf_dict_min)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(AyuSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.stats = crawler.stats

        # 先输出下相关日志，用于调试时查看
        spider.slog.debug(f"settings_type 配置: {cls.settings_type}")
        spider.slog.debug(f"scrapy 当前配置为: {dict(crawler.settings)}")

        # 1).先配置 Mysql 的相关信息，如果存在 Mysql 配置，则把 mysql_conf 添加到 spider 上
        if mysql_conf := cls.get_mysql_config(crawler.settings):
            spider.slog.info("项目中配置了 mysql_config 信息")
            spider.mysql_config = mysql_conf

            # 如果打开了 mysql_engine_enabled 参数(用于 spiders 中数据入库前去重查询)
            if cls.mysql_engine_enabled:
                mysql_url = (
                    f'mysql+pymysql://{mysql_conf.get("user")}'
                    f':{mysql_conf.get("password")}@{mysql_conf.get("host")}'
                    f':{mysql_conf.get("port")}/{mysql_conf.get("database")}'
                    f'?charset={mysql_conf.get("charset")}'
                )
                spider.mysql_engine = MySqlEngineClass(engine_url=mysql_url).engine

        # 2).配置 MongoDB 的相关信息，如果存在 MongoDB 配置，则把 mongodb_conf 添加到 spider 上
        if mongodb_conf := cls.get_mongodb_config(crawler.settings):
            spider.slog.info("项目中配置了 mongodb_config 信息")
            spider.mongodb_conf = mongodb_conf

        return spider
