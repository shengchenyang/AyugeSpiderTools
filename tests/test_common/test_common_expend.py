from ayugespidertools.common.expend import (
    MysqlPipeEnhanceMixin,
    OraclePipeEnhanceMixin,
    PostgreSQLPipeEnhanceMixin,
)
from ayugespidertools.common.typevars import MysqlConf
from tests import PYMYSQL_CONFIG


class TestDatabasePipeEnhanceMixin:
    def setup_method(self):
        self._table = "demo_one"
        self._item = {"nick_name": "zhangsan", "age": 18}
        self.mpem = MysqlPipeEnhanceMixin()
        self.ppem = PostgreSQLPipeEnhanceMixin()
        self.opem = OraclePipeEnhanceMixin()
        self._mysql_conf = MysqlConf(**PYMYSQL_CONFIG)

    def test_connect(self):
        self.mpem._connect(self._mysql_conf)

    def test_mysql_get_sql_by_item(self):
        odku_sql, args = self.mpem._get_sql_by_item(self._table, self._item)
        expect_odku_sql = (
            "INSERT INTO `demo_one` (`nick_name`, `age`) value"
            "s (%s, %s) ON DUPLICATE KEY UPDATE  `nick_name` = %s, `age` = %s"
        )
        assert odku_sql == expect_odku_sql, args == ("zhangsan", 18, "zhangsan", 18)
        no_odku_sql, args = self.mpem._get_sql_by_item(self._table, self._item, False)
        expect_no_odku_sql = (
            "INSERT INTO `demo_one` (`nick_name`, `age`) values (%s, %s)"
        )
        assert no_odku_sql == expect_no_odku_sql, args == ("zhangsan", 18)

    def test_postgresql_get_sql_by_item(self):
        sql = self.ppem._get_sql_by_item(self._table, self._item)
        assert sql == "INSERT INTO demo_one (nick_name, age) values (%s, %s);"

    def test_oracle_get_sql_by_item(self):
        sql = self.opem._get_sql_by_item(self._table, self._item)
        assert (
            sql
            == 'INSERT INTO "demo_one" ("nick_name", "age") values (:nick_name, :age)'
        )
