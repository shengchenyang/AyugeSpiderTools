from typing import Literal

import pymysql

__all__ = [
    "MysqlOrm",
]

SearchTypeStr = Literal["all", "one"]


class MysqlOrm:
    """数据库的简单使用，结合 SqlFormat 方法使用（临时使用）"""

    def __init__(self, pymsql_connect_conf: dict):
        self.conn = pymysql.connect(**pymsql_connect_conf)
        self.cursor = self.conn.cursor()

    def insert_data(self, sql_pre: str, sql_after: tuple):
        self.cursor.execute(sql_pre, sql_after)
        self.conn.commit()

    def search_data(
        self, sql_pre: str, sql_after: tuple, type: SearchTypeStr = "one"
    ) -> tuple:
        self.cursor.execute(sql_pre, sql_after)
        if type == "all":
            return self.cursor.fetchall()
        elif type == "one":
            return self.cursor.fetchone()

    def update_data(self, sql_pre: str, sql_after: tuple):
        self.cursor.execute(sql_pre, sql_after)
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def __del__(self):
        self.cursor.close()
        self.conn.close()
