from pathlib import Path

import pytest

from ayugespidertools.common.sqlformat import GenMysql
from ayugespidertools.mysqlclient import MysqlOrm
from tests import tests_sqlfiledir
from tests.conftest import PYMYSQL_CONFIG, test_table


@pytest.fixture(scope="module")
def mysql_first_step(mysql_db_cursor):
    # 前提准备，先创建需要的数据库数据表的测试数据
    mysql_db_cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS `{test_table}` (
          `id` int(32) NOT NULL AUTO_INCREMENT COMMENT 'id',
          `article_detail_url` varchar(255) DEFAULT '' COMMENT '文章详情链接',
          `article_title` varchar(255) DEFAULT '' COMMENT '文章标题',
          `comment_count` varchar(255) DEFAULT '' COMMENT '文章评论数量',
          `favor_count` varchar(255) DEFAULT '' COMMENT '文章赞成数量',
          `nick_name` varchar(255) DEFAULT '' COMMENT '文章作者昵称',
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试表示例';
        """
    )

    mysql_db_cursor.execute(f"SELECT COUNT(*) AS cnt FROM {test_table}")
    num = mysql_db_cursor.fetchone()[0]

    # 如果没有数据，就先插入示例数据
    if num <= 0:
        sql_file = Path(tests_sqlfiledir, "_test_article_info_table.sql")
        with sql_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("INSERT INTO"):
                    line = line.replace("_test_article_info_table", test_table)
                    mysql_db_cursor.execute(line.strip())


def test_select_data(mysql_first_step, mysql_db_cursor):
    select_sql, select_value = GenMysql.select_generate(
        db_table=test_table,
        key=["id", "article_title"],
        rule={"nick_name|=": "youcans_"},
        limit=1,
    )
    mysql_db_cursor.execute(select_sql, select_value)
    status, res = mysql_db_cursor.fetchone()
    assert status == 1, res == "【ChatGPT 视觉模型】Visual ChatGPT 深度解析"


def test_insert_data(mysql_first_step, mysql_db_cursor):
    insert_sql, insert_value = GenMysql.insert_generate(
        db_table=test_table,
        data={
            "article_detail_url": "https://blog.csdn.net/scm_2008/article/details/129387927",
            "article_title": "基于SpringBoot+SpringCloud+Vue前后端分离项目实战 --开篇",
            "comment_count": "160",
            "favor_count": "174",
            "nick_name": "天罡gg",
        },
    )
    mysql_db_cursor.execute(insert_sql, insert_value)

    # 插入后查询这条数据，如果搜索结果中存在一条及以上则正常
    select_sql, select_value = GenMysql.select_generate(
        db_table=test_table,
        key=["id", "article_title"],
        rule={
            "nick_name|=": "天罡gg",
            "article_title|=": "基于SpringBoot+SpringCloud+Vue前后端分离项目实战 --开篇",
        },
    )

    mysql_db_cursor.execute(select_sql, select_value)
    _select_res = mysql_db_cursor.fetchall()
    assert len(_select_res) >= 1


def test_update_data(mysql_first_step, mysql_db_cursor):
    _favor_count_updated = "100"
    update_sql, update_value = GenMysql.update_generate(
        db_table=test_table,
        data={"favor_count": _favor_count_updated},
        rule={"id": "1"},
    )
    mysql_db_cursor.execute(update_sql, update_value)

    # 更新后查询这条数据，如果确实修改则正常
    select_sql, select_value = GenMysql.select_generate(
        db_table=test_table,
        key=["id", "favor_count"],
        rule={"id|=": "1"},
    )

    mysql_db_cursor.execute(select_sql, select_value)
    _select_res = mysql_db_cursor.fetchall()
    assert _select_res[0][1] == _favor_count_updated


# 以上测试使用的是测试中的 mysql_db_cursor，以下真正使用的是库中的 MysqlOrm 来测试
@pytest.fixture(scope="class")
def mysqlorm_conn():
    conn = MysqlOrm(pymysql_connect_conf=PYMYSQL_CONFIG)
    yield conn
    conn.close()


class TestMysqlOrm:
    def test_mysqlorm_insert_data(self, mysqlorm_conn, mysql_db_cursor):
        insert_sql, insert_value = GenMysql.insert_generate(
            db_table=test_table,
            data={
                "article_detail_url": "https://blog.csdn.net/scm_2008/article/details/129387927",
                "article_title": "基于SpringBoot+SpringCloud+Vue前后端分离项目实战 --开篇",
                "comment_count": "160",
                "favor_count": "174",
                "nick_name": "天罡gg_ttt",
            },
        )
        mysqlorm_conn.insert_data(sql_pre=insert_sql, sql_after=insert_value)

        # 插入后查询这条数据，如果搜索结果中存在一条及以上则正常
        select_sql, select_value = GenMysql.select_generate(
            db_table=test_table,
            key=["id", "article_title"],
            rule={
                "nick_name|=": "天罡gg_ttt",
                "article_title|=": "基于SpringBoot+SpringCloud+Vue前后端分离项目实战 --开篇",
            },
        )

        mysql_db_cursor.execute(select_sql, select_value)
        _select_res = mysql_db_cursor.fetchall()
        assert len(_select_res) >= 1

    def test_mysqlorm_search_data(self, mysqlorm_conn, mysql_db_cursor):
        select_sql, select_value = GenMysql.select_generate(
            db_table=test_table,
            key=["id", "article_title"],
            rule={"nick_name|=": "youcans_"},
            limit=1,
        )
        status, res = mysqlorm_conn.search_data(
            sql_pre=select_sql, sql_after=select_value
        )
        assert status == 1, res == "【ChatGPT 视觉模型】Visual ChatGPT 深度解析"

    def test_mysqlorm_update_data(self, mysqlorm_conn, mysql_db_cursor):
        _favor_count_updated = "200"
        update_sql, update_value = GenMysql.update_generate(
            db_table=test_table,
            data={"favor_count": _favor_count_updated},
            rule={"id": "1"},
        )
        mysqlorm_conn.update_data(sql_pre=update_sql, sql_after=update_value)

        # 更新后查询这条数据，如果确实修改则正常
        select_sql, select_value = GenMysql.select_generate(
            db_table=test_table,
            key=["id", "favor_count"],
            rule={"id|=": "1"},
        )

        mysql_db_cursor.execute(select_sql, select_value)
        _select_res = mysql_db_cursor.fetchall()
        assert _select_res[0][1] == _favor_count_updated
