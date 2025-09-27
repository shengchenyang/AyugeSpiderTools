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
        odku_sql, args = self.mpem._get_sql_by_item(
            table=self._table, item=self._item, odku_enable=True
        )
        expect_odku_sql = "INSERT INTO `demo_one` (`nick_name`, `age`) values (%s, %s)"
        assert odku_sql == expect_odku_sql, args == ("zhangsan", 18)
        no_odku_sql, args = self.mpem._get_sql_by_item(self._table, self._item, False)
        expect_no_odku_sql = (
            "INSERT INTO `demo_one` (`nick_name`, `age`) values (%s, %s)"
        )
        assert no_odku_sql == expect_no_odku_sql, args == ("zhangsan", 18)
        sql, args = self.mpem._get_sql_by_item(
            self._table, self._item, True, duplicate={"age": 22}
        )
        expect_odku_sql = (
            "INSERT INTO `demo_one` (`nick_name`, `age`) values (%s, %s)"
            " ON DUPLICATE KEY UPDATE  `age` = %s"
        )
        assert sql == expect_odku_sql, args == ("zhangsan", 18, 22)

    def test_postgresql_get_sql_by_item(self):
        sql = self.ppem._get_sql_by_item(self._table, self._item)
        assert (
            sql
            == "INSERT INTO demo_one (nick_name, age) VALUES ($1, $2) ON CONFLICT DO NOTHING;"
        )
        sql = self.ppem._get_sql_by_item(self._table, self._item, is_psycopg=True)
        assert sql == "INSERT INTO demo_one (nick_name, age) values (%s, %s);"

    def test_oracle_get_sql_by_item(self):
        sql = self.opem._get_sql_by_item(self._table, self._item)
        assert (
            sql
            == 'INSERT INTO "demo_one" ("nick_name", "age") values (:nick_name, :age)'
        )
