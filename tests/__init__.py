import configparser
from pathlib import Path

tests_dir = Path(__file__).parent
tests_vitdir = str(Path(__file__).parent.resolve() / "VIT")
tests_sqlfiledir = str(Path(__file__).parent.resolve() / "docs/sqlfile")
config_parser = configparser.ConfigParser()
config_parser.read(f"{tests_vitdir}/.conf", encoding="utf-8")

# 测试环境中各种配置信息，已脱敏，请自行配置 VIT 的 .conf 文件后测试
mysql_conf = config_parser["mysql"]
mongodb_conf = config_parser["mongodb"]
oss_conf = config_parser["ali_oss"]

PYMYSQL_CONFIG = {
    "host": mysql_conf["host"],
    "port": mysql_conf.getint("port"),
    "user": mysql_conf["user"],
    "password": mysql_conf["password"],
    "database": mysql_conf["database"],
    "charset": mysql_conf["charset"],
    # "cursorclass": pymysql.cursors.Cursor,
}

MONGODB_CONFIG = {
    "host": mongodb_conf["host"],
    "port": mongodb_conf.getint("port"),
    "user": mongodb_conf["user"],
    "password": mongodb_conf["password"],
    "authsource": mongodb_conf["authsource"],
    "database": mongodb_conf["database"],
}

OSS_CONFIG = {
    "accesskeyid": oss_conf["accesskeyid"],
    "accesskeysecret": oss_conf["accesskeysecret"],
    "endpoint": oss_conf["endpoint"],
    "bucket": oss_conf["bucket"],
    "doc": oss_conf["doc"],
}

CONSUL_CONFIG = {
    "token": config_parser.get("consul", "token", fallback=None),
    "url": config_parser.get("consul", "url", fallback=None),
    "format": config_parser.get("consul", "format", fallback="json"),
}
