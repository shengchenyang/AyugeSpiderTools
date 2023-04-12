import copy

import pymysql
import pytest
from pymongo import MongoClient

from tests import MONGODB_CONFIG, PYMYSQL_CONFIG

test_table = "_test_article_info_table"
mongodb_database = MONGODB_CONFIG["database"]
mongodb_ori = copy.deepcopy(MONGODB_CONFIG)


class ForTestConfig:
    """
    用于测试需要的全局配置
    """

    # scrapy 默认配置
    scrapy_default_settings = {
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "FEED_EXPORT_ENCODING": "utf-8",
    }


@pytest.fixture(scope="session")
def mysql_db_conn():
    # 创建测试时可能需要的 mysql 数据库连接
    with pymysql.connect(**PYMYSQL_CONFIG) as conn:
        yield conn


@pytest.fixture(scope="session")
def mysql_db_cursor():
    # 创建测试时可能需要的 mysql 数据库 cursor 对象
    with pymysql.connect(**PYMYSQL_CONFIG, autocommit=True) as conn:
        with conn.cursor() as cursor:
            yield cursor

            # 清理 mysql 测试产生的数据
            cursor.execute(f"DROP TABLE IF EXISTS {test_table}")


@pytest.fixture(scope="session")
def mongodb_conn():
    database = MONGODB_CONFIG.pop("database")
    MONGODB_CONFIG.pop("authsource")
    MONGODB_CONFIG["username"] = MONGODB_CONFIG.pop("user")
    with MongoClient(**MONGODB_CONFIG) as conn:
        yield conn

        # 清理 mongodb 测试产生的数据
        conn[database][test_table].drop()
