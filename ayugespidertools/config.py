import configparser
import os
from os.path import abspath, dirname, join

from environs import Env
from loguru import logger

__all__ = [
    "NormalConfig",
    "logger",
]


env = Env()
env.read_env()


class NormalConfig(object):
    """
    用于存放此项目的通用配置，其实大部分就是用于测试文件使用
    """

    # 项目根目录及其它所需目录
    CONFIG_DIR = dirname(abspath(__file__))
    ROOT_DIR = os.path.dirname(CONFIG_DIR)
    LOG_DIR = join(CONFIG_DIR, "logs")
    DOC_DIR = join(CONFIG_DIR, "docs")
    COMMON_DIR = join(CONFIG_DIR, "common")
    VIT_DIR = join(CONFIG_DIR, "VIT")

    # 从应用配置管理获取配置，是否开启(选择 consul 方式，nacos 也是可以的，以后可能添加从 nacos 中获取配置的功能)
    APP_CONF_MANAGE = env.bool("APP_CONF_MANAGE", True)

    # 以下全为本库测试所依赖的配置，真实项目中是不需要的。若调试时需要以下配置，请打开 run_test_debugger 和修改 VIT 文件夹下的 .conf 文件
    if RUN_TEST_DEBUGGER := env.bool("RUN_TEST_DEBUGGER", False):
        # 加载秘钥等配置信息
        config_parser = configparser.ConfigParser()
        config_parser.read(f"{VIT_DIR}/.conf", encoding="utf-8")
        # 测试环境中各种配置信息，已脱敏，请自行配置 VIT 的 .conf 文件后测试
        mysql_config = config_parser["MYSQL"]
        mongodb_config = config_parser["MONGODB"]
        oss_config = config_parser["ALI_OSS"]
        # 企业微信机器人 key
        WWXRobot_key = config_parser["WWXRobot"]["key"]

        # 测试 Mysql 数据库配置
        PYMYSQL_CONFIG = {
            "host": mysql_config["HOST"],
            "port": mysql_config.getint("PORT"),
            "user": mysql_config["USER"],
            "password": mysql_config["PASSWORD"],
            "database": mysql_config["DATABASE"],
            "charset": mysql_config["CHARSET"],
            # "cursorclass": pymysql.cursors.Cursor,
        }

        # 测试 MongoDB 数据库配置
        MONGODB_CONFIG = {
            "host": mongodb_config["HOST"],
            "port": mongodb_config.getint("PORT"),
            "user": mongodb_config["USER"],
            "password": mongodb_config["PASSWORD"],
            "authsource": mongodb_config["AUTHSOURCE"],
            "database": mongodb_config["DATABASE"],
        }

        # 测试 MongoDB 数据库配置
        MONGODB_CONN_URI = config_parser["MONGODB_URI"]["CONN_URI"]

        # 读取 Oss 配置信息，已脱敏，请自行配置后测试
        OSS_CONFIG = {
            "OssAccessKeyId": oss_config["OSSACCESSKEYID"],
            "OssAccessKeySecret": oss_config["OSSACCESSKEYSECRET"],
            "Endpoint": oss_config["ENDPOINT"],
            "examplebucket": oss_config["EXAMPLEBUCKET"],
            "operateDoc": oss_config["OPERATEDOC"],
        }
