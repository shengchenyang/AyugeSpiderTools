from ayugespidertools.common.sqlformat import GenMysql


def test_select_generate():
    select_sql, select_value = GenMysql.select_generate(
        db_table="student", key=["id"], rule={"age|=": 18, "sex|!=": "male"}, limit=1
    )
    print("select_sql:", select_sql)
    print("select_value:", select_value)
    assert select_sql, select_value


def test_insert_generate():
    insert_sql, insert_value = GenMysql.insert_generate(
        db_table="student", data={"name": "zhangsan", "age": 18}
    )
    print("insert_sql:", insert_sql)
    print("insert_value:", insert_value)
    assert insert_sql, insert_value


def test_update_generate():
    update_sql, update_value = GenMysql.update_generate(
        db_table="student", data={"score": 4}, rule={"name": "zhangsan"}
    )
    print("update_sql:", update_sql)
    print("update_value:", update_value)
    assert update_sql, update_value
