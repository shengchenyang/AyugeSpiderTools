import re
import textwrap

import pytest

from ayugespidertools.common.sqlformat import (
    GenMysql,
    GenOracle,
    GenPostgresql,
    GenPostgresqlAsyncpg,
)
from ayugespidertools.common.typevars import sentinel


def format_str(data: str) -> str:
    return re.sub(r"\s+", " ", textwrap.dedent(data)).strip()


@pytest.mark.parametrize(
    ("generator", "expected_sql"),
    [
        (GenMysql, "select `name`, `age`, `title` from articles"),
        (GenPostgresql, "select name, age, title from articles"),
        (GenPostgresqlAsyncpg, "SELECT name, age, title FROM articles"),
        (GenOracle, 'select "name", "age", "title" from "articles"'),
    ],
)
@pytest.mark.parametrize("vertical", [True, False])
def test_select_without_rule_or_limit(generator, expected_sql, vertical):
    sql, args = generator.select_generate(
        db_table="articles",
        key=["name", "age", "title"],
        rule={},
        vertical=vertical,
    )
    assert sql == expected_sql
    assert args == ()


@pytest.mark.parametrize(
    ("generator", "sql_template"),
    [
        (GenMysql, "select {} from articles"),
        (GenPostgresql, "select {} from articles"),
        (GenPostgresqlAsyncpg, "SELECT {} FROM articles"),
    ],
)
@pytest.mark.parametrize("expression", ["1", "count(*)", "count(1)"])
def test_select_single_expression(generator, sql_template, expression):
    sql, args = generator.select_generate(
        db_table="articles",
        key=[expression],
        rule={},
    )
    assert sql == sql_template.format(expression)
    assert args == ()


@pytest.mark.parametrize(
    ("generator", "expected_sql"),
    [
        (
            GenMysql,
            "select `id` from articles where `age`=%s or `title`=%s order by id DESC",
        ),
        (
            GenPostgresql,
            "select id from articles where age=%s or title=%s order by id DESC",
        ),
        (
            GenPostgresqlAsyncpg,
            "SELECT id FROM articles WHERE age=$1 or title=$2 ORDER BY id DESC",
        ),
    ],
)
def test_select_with_order_by(generator, expected_sql):
    sql, args = generator.select_generate(
        db_table="articles",
        key=["id"],
        rule={"age": 18, "title": "标题"},
        base="or",
        order_by="id DESC",
        vertical=False,
    )
    assert sql == expected_sql
    assert args == (18, "标题")


@pytest.mark.parametrize(
    ("generator", "expected_sql"),
    [
        (
            GenPostgresql,
            "INSERT INTO articles (title, url) VALUES (%s, %s) ON CONFLICT (title) DO NOTHING;",
        ),
        (
            GenPostgresqlAsyncpg,
            "INSERT INTO articles (title, url) VALUES ($1, $2) ON CONFLICT (title) DO NOTHING;",
        ),
    ],
)
@pytest.mark.parametrize("update_cols", [None, set()])
def test_upsert_without_update_columns(generator, expected_sql, update_cols):
    sql, args = generator.upsert_generate(
        db_table="articles",
        conflict_cols={"title"},
        data={"title": "标题", "url": "https://example.com/'"},
        update_cols=update_cols,
    )
    assert sql == expected_sql
    assert args == ("标题", "https://example.com/'")
    assert args[1] not in sql


def test_mysql_select_generate():
    sql, value = GenMysql.select_generate(
        db_table="student", key=["id"], rule={"age|=": 18, "sex|!=": "male"}, limit=1
    )
    assert sql == "select `id` from student where `age`=%s and `sex`!=%s limit 1"
    assert value == (18, "male")

    sql, value = GenMysql.select_generate(
        db_table="student",
        key=["id"],
        rule={"age=": 18, "sex": "male"},
        limit=1,
        vertical=False,
    )
    assert sql == "select `id` from student where `age=`=%s and `sex`=%s limit 1"
    assert value == (18, "male")


def test_mysql_insert_generate():
    sql, value = GenMysql.insert_generate(
        db_table="student", data={"name": "zhangsan", "age": 18}
    )
    assert sql == "insert into `student` (`name`, `age`) values (%s, %s)"
    assert value == ("zhangsan", 18)


def test_mysql_update_generate():
    sql, value = GenMysql.update_generate(
        db_table="student", data={"score": 4}, rule={"name": "zhangsan"}
    )
    assert sql == "update `student` set `score`=%s where `name`=%s"
    assert value == (4, "zhangsan")


def test_postgresql_select_generate():
    sql, value = GenPostgresql.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age|=": 18}, limit=1, vertical=True
    )
    assert sql == "select id from demo_eleven where age=%s limit 1"
    assert value == (18,)
    sql, value = GenPostgresql.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age": 18}, limit=1, vertical=False
    )
    assert sql == "select id from demo_eleven where age=%s limit 1"
    assert value == (18,)


def test_postgresql_insert_generate():
    sql, value = GenPostgresql.insert_generate(
        db_table="demo_eleven", data={"name": "zhangsan", "age": 18}
    )
    assert sql == "insert into demo_eleven (name, age) values (%s, %s)"
    assert value == ("zhangsan", 18)


def test_postgresql_update_generate():
    sql, value = GenPostgresql.update_generate(
        db_table="demo_eleven", data={"score": 4}, rule={"name": "zhangsan"}
    )
    assert sql == "update demo_eleven set score=%s where name=%s"
    assert value == (4, "zhangsan")


def test_postgresql_upsert_generate():
    sql, value = GenPostgresql.upsert_generate(
        db_table="demo_eleven",
        conflict_cols={"id"},
        data={"name": "zhangsan", "age": 18},
        update_cols={"age"},
    )
    assert (
        sql
        == "INSERT INTO demo_eleven (name, age) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET age = EXCLUDED.age;"
    )
    assert value == ("zhangsan", 18)


def test_postgres_asyncpg_select_generate():
    sql, value = GenPostgresqlAsyncpg.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age|=": 18}, limit=1, vertical=True
    )
    assert sql == "SELECT id FROM demo_eleven WHERE age=$1 LIMIT 1"
    assert value == (18,)
    sql, value = GenPostgresqlAsyncpg.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age": 18}, limit=1, vertical=False
    )
    assert sql == "SELECT id FROM demo_eleven WHERE age=$1 LIMIT 1"
    assert value == (18,)


def test_postgres_asyncpg_insert_generate():
    sql, value = GenPostgresqlAsyncpg.insert_generate(
        db_table="demo_eleven", data={"name": "zhangsan", "age": 18}
    )
    assert sql == "INSERT INTO demo_eleven (name, age) VALUES ($1, $2)"
    assert list(value) == ["zhangsan", 18]


def test_postgres_asyncpg_update_generate():
    sql, value = GenPostgresqlAsyncpg.update_generate(
        db_table="demo_eleven", data={"score": 4}, rule={"name": "zhangsan"}
    )
    assert sql == "UPDATE demo_eleven SET score=$1 WHERE name=$2"
    assert value == (4, "zhangsan")


def test_postgres_asyncpg_upsert_generate():
    sql, value = GenPostgresqlAsyncpg.upsert_generate(
        db_table="demo_eleven",
        conflict_cols={"id"},
        data={"name": "zhangsan", "age": 18},
        update_cols={"age"},
    )
    assert (
        sql
        == "INSERT INTO demo_eleven (name, age) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET age = EXCLUDED.age;"
    )
    assert value == ("zhangsan", 18)


def test_postgresql_psycopg_merge_generate():
    sql, args = GenPostgresql.merge_generate(
        db_table="articles",
        match_cols={"title": "标题", "platform": "web"},
        data={"title": "标题", "platform": "web", "url": "https://example.com/'"},
        update_cols={"url"},
    )
    assert format_str(sql) == (
        "MERGE INTO articles AS t "
        "USING (VALUES (%s, %s, %s)) AS s(title, platform, url) "
        "ON t.title = s.title AND t.platform = s.platform "
        "WHEN MATCHED THEN UPDATE SET url = s.url "
        "WHEN NOT MATCHED THEN INSERT (title, platform, url) "
        "VALUES (s.title, s.platform, s.url)"
    )
    assert args == ("标题", "web", "https://example.com/'")
    assert args[2] not in sql


@pytest.mark.parametrize("update_cols", [None, set()])
def test_postgresql_psycopg_merge_skips_matched_rows(update_cols):
    sql, args = GenPostgresql.merge_generate(
        db_table="articles",
        match_cols={"title"},
        data={"title": "标题", "url": "link"},
        update_cols=update_cols,
    )
    assert format_str(sql) == (
        "MERGE INTO articles AS t "
        "USING (VALUES (%s, %s)) AS s(title, url) ON t.title = s.title "
        "WHEN NOT MATCHED THEN INSERT (title, url) VALUES (s.title, s.url)"
    )
    assert args == ("标题", "link")


@pytest.mark.parametrize("match_cols", [None, {}, []])
def test_postgresql_psycopg_merge_without_rule_inserts(match_cols):
    sql, args = GenPostgresql.merge_generate(
        db_table="articles",
        match_cols=match_cols,
        data={"title": "标题", "url": "link"},
        update_cols={"url"},
    )
    assert sql == (
        "INSERT INTO articles (title, url) VALUES (%s, %s) ON CONFLICT DO NOTHING;"
    )
    assert args == ("标题", "link")


@pytest.mark.parametrize("match_cols", [None, {}, [], set(), ()])
@pytest.mark.parametrize("update_cols", [None, {"url"}])
def test_postgresql_asyncpg_merge_without_rule_inserts(match_cols, update_cols):
    sql, args = GenPostgresqlAsyncpg.merge_generate(
        db_table="articles",
        match_cols=match_cols,
        data={"title": "标题", "url": "https://example.com/'"},
        update_cols=update_cols,
    )
    assert sql == (
        "INSERT INTO articles (title, url) VALUES ($1, $2) ON CONFLICT DO NOTHING;"
    )
    assert args == ("标题", "https://example.com/'")
    assert args[1] not in sql


@pytest.mark.parametrize("update_cols", [None, set()])
def test_postgresql_asyncpg_merge_skips_matched_rows(update_cols):
    sql, args = GenPostgresqlAsyncpg.merge_generate(
        db_table="articles",
        match_cols={"title"},
        data={"title": "标题", "url": "link"},
        update_cols=update_cols,
    )
    assert format_str(sql) == (
        "MERGE INTO articles AS t "
        "USING (VALUES ($1, $2)) AS s(title, url) ON t.title = s.title "
        "WHEN NOT MATCHED THEN INSERT (title, url) VALUES (s.title, s.url)"
    )
    assert args == ("标题", "link")


def test_postgresql_merge_generate():
    sql, value = GenPostgresqlAsyncpg.merge_generate(
        db_table="demo_eleven",
        match_cols=["octree_text"],
        data={"octree_text": "zs", "octree_href": "new@mail.com"},
        update_cols=["octree_href"],
    )
    sql = format_str(data=sql)
    assert (
        sql
        == "MERGE INTO demo_eleven AS t USING (VALUES ($1, $2)) AS s(octree_text, octree_href) ON t.octree_text = s.octree_text WHEN MATCHED THEN UPDATE SET octree_href = s.octree_href WHEN NOT MATCHED THEN INSERT (octree_text, octree_href) VALUES (s.octree_text, s.octree_href)"
    )
    assert value == ("zs", "new@mail.com")


def test_oracle_select_generate():
    sql, value = GenOracle.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age": 18}, limit=1, vertical=False
    )
    assert sql == (
        'select * from (select "id" from "demo_eleven" where "age"=:1) '
        "where ROWNUM <= 1"
    )
    assert value == (18,)

    sql, value = GenOracle.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age|=": 18}, limit=1, vertical=True
    )
    assert sql == (
        'select * from (select "id" from "demo_eleven" where "age"=:1) '
        "where ROWNUM <= 1"
    )
    assert value == (18,)


@pytest.mark.parametrize(
    ("rule", "where_sql", "expected_args"),
    [
        ({}, "", ()),
        (
            {"age": 18, "title": "标题"},
            ' where "age"=:1 or "title"=:2',
            (18, "标题"),
        ),
    ],
)
@pytest.mark.parametrize("order_by", [None, "id"])
@pytest.mark.parametrize("limit", [sentinel, 0, 1, 10])
def test_oracle_select_limit(rule, where_sql, expected_args, order_by, limit):
    sql, args = GenOracle.select_generate(
        db_table="articles",
        key=["id", "title"],
        rule=rule,
        base="or",
        order_by=order_by,
        limit=limit,
        vertical=False,
    )
    expected_query = f'select "id", "title" from "articles"{where_sql}'
    if order_by:
        expected_query += ' order by "id"'
    if limit is not sentinel:
        expected_sql = f"select * from ({expected_query}) where ROWNUM <= {limit}"
    else:
        expected_sql = expected_query
    assert sql == expected_sql
    assert args == expected_args


@pytest.mark.parametrize("column", ["id", "VideoId", "视频ID"])
def test_oracle_select_order_by_column(column):
    sql, args = GenOracle.select_generate(
        db_table="articles",
        key=[column],
        rule={"title": "标题"},
        order_by=column,
        vertical=False,
    )
    assert sql == (
        f'select "{column}" from "articles" where "title"=:1 order by "{column}"'
    )
    assert args == ("标题",)


def test_oracle_update_generate():
    sql, value = GenOracle.update_generate(
        db_table="demo_eleven",
        data={"name": "zhangsan", "age": 18},
        rule={"name": "zhangsan"},
    )
    assert sql == 'update "demo_eleven" set "name"=:1, "age"=:2 where "name"=:3'
    assert value == ("zhangsan", 18, "zhangsan")


@pytest.mark.parametrize("match_cols", [None, {}, [], set(), ()])
@pytest.mark.parametrize("update_cols", [None, {"url"}])
def test_oracle_merge_without_rule_inserts(match_cols, update_cols):
    sql, args = GenOracle.merge_generate(
        db_table="articles",
        match_cols=match_cols,
        data={"title": "标题", "url": "https://example.com/'"},
        update_cols=update_cols,
    )
    assert sql == 'INSERT INTO "articles" ("title", "url") VALUES (:1, :2)'
    assert args == ("标题", "https://example.com/'")
    assert args[1] not in sql


@pytest.mark.parametrize("update_cols", [None, set()])
def test_oracle_merge_skips_matched_rows(update_cols):
    sql, args = GenOracle.merge_generate(
        db_table="articles",
        match_cols=["title", "platform"],
        data={"title": "标题", "platform": "web", "url": "https://example.com/'"},
        update_cols=update_cols,
    )
    assert format_str(sql) == (
        'MERGE INTO "articles" t '
        'USING (SELECT :1 "title", :2 "platform", :3 "url" FROM dual) s '
        'ON (t."title" = s."title" AND t."platform" = s."platform") '
        'WHEN NOT MATCHED THEN INSERT ("title", "platform", "url") '
        'VALUES (s."title", s."platform", s."url")'
    )
    assert args == ("标题", "web", "https://example.com/'")
    assert args[2] not in sql


def test_oracle_merge_generate():
    sql, value = GenOracle.merge_generate(
        db_table="demo_eleven",
        match_cols=["octree_text"],
        data={"octree_text": "zs", "octree_href": "new@mail.com"},
        update_cols=["octree_href"],
    )
    sql = format_str(data=sql)
    assert (
        sql
        == 'MERGE INTO "demo_eleven" t USING (SELECT :1 "octree_text", :2 "octree_href" FROM dual) s ON (t."octree_text" = s."octree_text") WHEN MATCHED THEN UPDATE SET t."octree_href" = s."octree_href" WHEN NOT MATCHED THEN INSERT ("octree_text", "octree_href") VALUES (s."octree_text", s."octree_href")'
    )
    assert value == ("zs", "new@mail.com")
