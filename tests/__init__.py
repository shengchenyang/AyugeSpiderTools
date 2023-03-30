import configparser
from pathlib import Path

tests_dir = Path(__file__).parent
tests_vitdir = str(Path(__file__).parent.resolve() / "VIT")
tests_sqlfiledir = str(Path(__file__).parent.resolve() / "docs/sqlfile")
config_parser = configparser.ConfigParser()
config_parser.read(f"{tests_vitdir}/.conf", encoding="utf-8")

# 测试环境中各种配置信息，已脱敏，请自行配置 VIT 的 .conf 文件后测试
mysql_conf = config_parser["MYSQL"]
mongodb_conf = config_parser["MONGODB"]
oss_conf = config_parser["ALI_OSS"]

# 测试 Mysql 数据库配置
PYMYSQL_CONFIG = {
    "host": mysql_conf["HOST"],
    "port": mysql_conf.getint("PORT"),
    "user": mysql_conf["USER"],
    "password": mysql_conf["PASSWORD"],
    "database": mysql_conf["DATABASE"],
    "charset": mysql_conf["CHARSET"],
    # "cursorclass": pymysql.cursors.Cursor,
}

# 测试 MongoDB 数据库配置
MONGODB_CONFIG = {
    "host": mongodb_conf["HOST"],
    "port": mongodb_conf.getint("PORT"),
    "user": mongodb_conf["USER"],
    "password": mongodb_conf["PASSWORD"],
    "authsource": mongodb_conf["AUTHSOURCE"],
    "database": mongodb_conf["DATABASE"],
}

# 测试 MongoDB 数据库配置
MONGODB_CONN_URI = config_parser["MONGODB_URI"]["CONN_URI"]

# 读取 Oss 配置信息，已脱敏，请自行配置后测试
OSS_CONFIG = {
    "OssAccessKeyId": oss_conf["OSSACCESSKEYID"],
    "OssAccessKeySecret": oss_conf["OSSACCESSKEYSECRET"],
    "Endpoint": oss_conf["ENDPOINT"],
    "examplebucket": oss_conf["EXAMPLEBUCKET"],
    "operateDoc": oss_conf["OPERATEDOC"],
}

# consul 应用管理的连接配置
CONSUL_CONFIG = {
    "TOKEN": config_parser.get("CONSUL", "TOKEN", fallback=None),
    "URL": config_parser.get("CONSUL", "URL", fallback=None),
    "FORMAT": config_parser.get("CONSUL", "FORMAT", fallback="json"),
}
