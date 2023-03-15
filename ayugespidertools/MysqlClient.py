from typing import Literal, Optional

import pymysql

__all__ = [
    "MysqlOrm",
]

SearchTypeStr = Literal["all", "one"]


class MysqlOrm(object):
    """数据库的简单使用，结合 SqlFormat 方法使用（临时使用）"""

    def __init__(self, pymsql_connect_config: dict):
        self.connection = pymysql.connect(**pymsql_connect_config)
        self.cursor = self.connection.cursor()

    def insert_data(self, sql_pre: str, sql_after: tuple):
        self.connection.ping(reconnect=True)
        self.cursor.execute(sql_pre, sql_after)
        self.connection.commit()

    def search_data(
        self, sql_pre: str, sql_after: tuple, type: SearchTypeStr = "one"
    ) -> tuple:
        self.connection.ping(reconnect=True)
        self.cursor.execute(sql_pre, sql_after)
        if type == "all":
            return self.cursor.fetchall()
        elif type == "one":
            return self.cursor.fetchone()

    def update_data(self, sql_pre: str, sql_after: tuple):
        self.connection.ping(reconnect=True)
        self.cursor.execute(sql_pre, sql_after)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def __del__(self):
        self.cursor.close()
        self.connection.close()
