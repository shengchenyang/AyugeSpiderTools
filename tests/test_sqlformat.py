import re
import textwrap

from ayugespidertools.common.sqlformat import GenMysql


def format_str(data: str) -> str:
    return re.sub(r"\s+", " ", textwrap.dedent(data)).strip()


def test_select_generate():
    select_sql, select_value = GenMysql.select_generate(
        db_table="student", key=["id"], rule={"age|=": 18, "sex|!=": "male"}, limit=1
    )
    assert select_sql == "select `id` from student where `age`=%s and `sex`!=%s limit 1"
    assert select_value == (18, "male")


def test_insert_generate():
    insert_sql, insert_value = GenMysql.insert_generate(
        db_table="student", data={"name": "zhangsan", "age": 18}
    )
    assert insert_sql == "insert into `student` (`name`, `age`) values (%s, %s)"
    assert insert_value == ("zhangsan", 18)


def test_update_generate():
    update_sql, update_value = GenMysql.update_generate(
        db_table="student", data={"score": 4}, rule={"name": "zhangsan"}
    )
    assert update_sql == "update `student` set `score`=%s where `name`=%s"
    assert update_value == (4, "zhangsan")


def test_postgresql_merge():
    from ayugespidertools.common.sqlformat import GenPostgresqlAsyncpg

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

    sql, value = GenPostgresqlAsyncpg.merge_generate(
        db_table="demo_eleven",
        match_cols=["octree_href"],
        data={"octree_text": "zs", "octree_href": "new@mail.com"},
        update_cols=["octree_text"],
    )
    sql = format_str(data=sql)
    assert (
        sql
        == "MERGE INTO demo_eleven AS t USING (VALUES ($1, $2)) AS s(octree_text, octree_href) ON t.octree_href = s.octree_href WHEN MATCHED THEN UPDATE SET octree_text = s.octree_text WHEN NOT MATCHED THEN INSERT (octree_text, octree_href) VALUES (s.octree_text, s.octree_href)"
    )
    assert value == ("zs", "new@mail.com")

    sql, value = GenPostgresqlAsyncpg.upsert_generate(
        db_table="demo_eleven",
        conflict_cols={"octree_text"},
        data={"octree_text": "zs", "octree_href": "new@mail.com"},
        update_cols={"octree_href"},
    )
    assert (
        sql
        == "INSERT INTO demo_eleven (octree_text, octree_href) VALUES ($1, $2) ON CONFLICT (octree_text) DO UPDATE SET octree_href = EXCLUDED.octree_href;"
    )
    assert value == ("zs", "new@mail.com")
