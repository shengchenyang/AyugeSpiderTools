import re
import textwrap

from ayugespidertools.common.sqlformat import (
    GenMysql,
    GenOracle,
    GenPostgresql,
    GenPostgresqlAsyncpg,
)


def format_str(data: str) -> str:
    return re.sub(r"\s+", " ", textwrap.dedent(data)).strip()


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
    assert sql == 'select `id` from "demo_eleven" where "age"=:1 AND ROWNUM = 1'
    assert value == (18,)

    sql, value = GenOracle.select_generate(
        db_table="demo_eleven", key=["id"], rule={"age|=": 18}, limit=1, vertical=True
    )
    assert sql == 'select `id` from "demo_eleven" where "age"=:1 AND ROWNUM = 1'
    assert value == (18,)


def test_oracle_update_generate():
    sql, value = GenOracle.update_generate(
        db_table="demo_eleven",
        data={"name": "zhangsan", "age": 18},
        rule={"name": "zhangsan"},
    )
    assert sql == 'update "demo_eleven" set "name"=:1, "age"=:2 where "name"=:3'
    assert value == ("zhangsan", 18, "zhangsan")


def test_oracle_upsert_generate():
    sql, value = GenOracle.upsert_generate(
        db_table="demo_eleven",
        conflict_cols={"id"},
        data={"name": "zhangsan", "age": 18},
        update_cols={"age"},
    )
    assert (
        sql
        == 'INSERT INTO "demo_eleven" ("name", "age") VALUES (:1, :2) ON CONFLICT (id) DO UPDATE SET age = EXCLUDED.age'
    )
    assert value == ("zhangsan", 18)


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
