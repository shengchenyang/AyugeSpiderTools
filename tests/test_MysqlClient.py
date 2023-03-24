import pytest

from ayugespidertools import MysqlClient
from ayugespidertools.common.SqlFormat import AboutSql
from tests import PYMYSQL_CONFIG, tests_sqlfiledir

mysql_client = MysqlClient.MysqlOrm(PYMYSQL_CONFIG)
test_table = "_test_article_info_table"


@pytest.fixture(scope="module")
def first_step():
    # 前提准备，先创建需要的数据库数据表的测试数据
    mysql_client.cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS `{test_table}` (
          `id` int(32) NOT NULL AUTO_INCREMENT COMMENT 'id',
          `article_detail_url` varchar(190) DEFAULT '' COMMENT '文章详情链接',
          `article_title` varchar(190) DEFAULT '' COMMENT '文章标题',
          `comment_count` varchar(190) DEFAULT '' COMMENT '文章评论数量',
          `favor_count` varchar(190) DEFAULT '' COMMENT '文章赞成数量',
          `nick_name` varchar(190) DEFAULT '' COMMENT '文章作者昵称',
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测试表示例';
        """
    )

    # 如果没有数据，就先插入示例数据
    mysql_client.cursor.execute(f"SELECT COUNT(*) AS cnt FROM {test_table}")
    num = mysql_client.cursor.fetchone()[0]

    if num <= 0:
        with open(f"{tests_sqlfiledir}/_article_info_table.sql", "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("INSERT INTO"):
                    mysql_client.cursor.execute(line.strip())
                    mysql_client.connection.commit()


def test_select_data(first_step):
    select_sql, select_value = AboutSql.select_generate(
        db_table=test_table,
        key=["id", "article_title"],
        rule={"nick_name|=": "youcans_"},
        limit=1,
    )
    status, res = mysql_client.search_data(select_sql, select_value, type="one")
    assert all([status == 1, res == "【ChatGPT 视觉模型】Visual ChatGPT 深度解析"])


def test_insert_data(first_step):
    insert_sql, insert_value = AboutSql.insert_generate(
        db_table=test_table,
        data={
            "article_detail_url": "https://blog.csdn.net/scm_2008/article/details/129387927",
            "article_title": "基于SpringBoot+SpringCloud+Vue前后端分离项目实战 --开篇",
            "comment_count": "160",
            "favor_count": "174",
            "nick_name": "天罡gg",
        },
    )
    mysql_client.insert_data(insert_sql, insert_value)

    # 插入后查询这条数据，如果搜索结果中存在一条及以上则正常
    select_sql, select_value = AboutSql.select_generate(
        db_table=test_table,
        key=["id", "article_title"],
        rule={
            "nick_name|=": "天罡gg",
            "article_title|=": "基于SpringBoot+SpringCloud+Vue前后端分离项目实战 --开篇",
        },
    )

    _select_res = mysql_client.search_data(select_sql, select_value, type="all")
    assert len(_select_res) >= 1


def test_update_data(first_step):
    _favor_count_updated = "100"
    update_sql, update_value = AboutSql.update_generate(
        db_table=test_table,
        data={"favor_count": _favor_count_updated},
        rule={"id": "1"},
    )
    mysql_client.update_data(update_sql, update_value)

    # 更新后查询这条数据，如果确实修改则正常
    select_sql, select_value = AboutSql.select_generate(
        db_table=test_table,
        key=["id", "favor_count"],
        rule={"id|=": "1"},
    )

    _select_res = mysql_client.search_data(select_sql, select_value, type="all")
    assert _select_res[0][1] == _favor_count_updated
