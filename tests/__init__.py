import configparser
from pathlib import Path

tests_vitdir = str(Path(__file__).parent.resolve() / "VIT")
config_parser = configparser.ConfigParser()
config_parser.read(f"{tests_vitdir}/.conf", encoding="utf-8")

# 测试环境中各种配置信息，已脱敏，请自行配置 VIT 的 .conf 文件后测试
mysql_config = config_parser["MYSQL"]
mongodb_config = config_parser["MONGODB"]
oss_config = config_parser["ALI_OSS"]

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
