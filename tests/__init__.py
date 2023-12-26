import configparser
from pathlib import Path

tests_dir = Path(__file__).parent
tests_vitdir = str(Path(__file__).parent.resolve() / "VIT")
tests_sqlfiledir = str(Path(__file__).parent.resolve() / "docs/sqlfile")
cfg = configparser.ConfigParser()
cfg.read(f"{tests_vitdir}/.conf", encoding="utf-8")

mysql_conf = cfg["mysql"]
mongodb_conf = cfg["mongodb"]
mongodb_uri_conf = cfg["mongodb:uri"]

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
    "authMechanism": mongodb_conf.get("authMechanism", "SCRAM-SHA-1"),
    "database": mongodb_conf["database"],
    "uri": mongodb_uri_conf.get("uri"),
}

CONSUL_CONFIG = {
    "token": cfg.get("consul", "token", fallback=None),
    "url": cfg.get("consul", "url", fallback=None),
    "format": cfg.get("consul", "format", fallback="json"),
}
