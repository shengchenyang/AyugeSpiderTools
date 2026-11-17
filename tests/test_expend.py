import pytest

from ayugespidertools.common.expend import (
    MysqlPipeEnhanceMixin,
    OraclePipeEnhanceMixin,
    PostgreSQLPipeEnhanceMixin,
)


@pytest.mark.parametrize(
    ("item", "expected_sql", "expected_args"),
    [
        (
            {"nick_name": "zs", "age": None, "enabled": False},
            "INSERT INTO `demo_one` (`nick_name`, `age`, `enabled`) "
            "values (%s, %s, %s)",
            ("zs", None, False),
        ),
    ],
)
def test_mysql_get_sql_by_item(item, expected_sql, expected_args):
    sql, args = MysqlPipeEnhanceMixin._get_sql_by_item("demo_one", item)

    assert sql == expected_sql
    assert args == expected_args


@pytest.mark.parametrize("insert_prefix", ["INSERT", "INSERT IGNORE"])
@pytest.mark.parametrize("odku_enable", [True, False])
@pytest.mark.parametrize(
    ("duplicate", "expected_update", "expected_update_args"),
    [
        (None, "", ()),
        ({}, "", ()),
        (
            {"age": None, "nick_name": "zs"},
            " ON DUPLICATE KEY UPDATE  `age` = %s, `nick_name` = %s",
            (None, "zs"),
        ),
    ],
)
def test_mysql_get_sql_by_item_insert_options(
    insert_prefix, odku_enable, duplicate, expected_update, expected_update_args
):
    sql, args = MysqlPipeEnhanceMixin._get_sql_by_item(
        "demo_one",
        {"nick_name": "zhangsan", "age": 18},
        odku_enable=odku_enable,
        insert_prefix=insert_prefix,
        duplicate=duplicate,
    )

    expected_sql = (
        f"{insert_prefix} INTO `demo_one` (`nick_name`, `age`) values (%s, %s)"
    )
    expected_args = ("zhangsan", 18)
    if odku_enable:
        expected_sql += expected_update
        expected_args += expected_update_args

    assert sql == expected_sql
    assert args == expected_args


def test_mysql_get_sql_by_item_duplicate_enabled_by_default():
    sql, args = MysqlPipeEnhanceMixin._get_sql_by_item(
        "demo_one", {"nick_name": "zhangsan", "age": 18}, duplicate={"age": 22}
    )

    assert sql == (
        "INSERT INTO `demo_one` (`nick_name`, `age`) values (%s, %s)"
        " ON DUPLICATE KEY UPDATE  `age` = %s"
    )
    assert args == ("zhangsan", 18, 22)


@pytest.mark.parametrize(
    ("item", "expected_asyncpg_sql", "expected_psycopg_sql"),
    [
        (
            {"nick_name": "zs", "age": None, "enabled": False},
            "INSERT INTO demo_one (nick_name, age, enabled) "
            "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING;",
            "INSERT INTO demo_one (nick_name, age, enabled) values (%s, %s, %s);",
        ),
    ],
)
def test_postgresql_get_sql_by_item(item, expected_asyncpg_sql, expected_psycopg_sql):
    sql = PostgreSQLPipeEnhanceMixin._get_sql_by_item("demo_one", item)
    assert sql == expected_asyncpg_sql

    sql = PostgreSQLPipeEnhanceMixin._get_sql_by_item("demo_one", item, is_psycopg=True)
    assert sql == expected_psycopg_sql


@pytest.mark.parametrize(
    ("item", "expected_sql"),
    [
        (
            {"nick_name": "zs", "age": None, "enabled": False},
            'INSERT INTO "DemoOne" ("nick_name", "age", "enabled") '
            "values (:nick_name, :age, :enabled)",
        ),
    ],
)
def test_oracle_get_sql_by_item(item, expected_sql):
    sql = OraclePipeEnhanceMixin._get_sql_by_item("DemoOne", item)

    assert sql == expected_sql
