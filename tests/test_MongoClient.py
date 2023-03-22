import json
import uuid

import pytest

from ayugespidertools.MongoClient import MongoDbBase
from tests import tests_dir
from tests.conftest import mongodb_database, mongodb_ori, test_table

add_data_list = [
    {
        # _id 参数可填可不填，如果不填则自动生成一个 ObjectId 类型的 id
        # "_id": "6412c83da7380bfe607aae20",
        "article_detail_url": "https://blog.csdn.net/weixin_70280523/article/details/129507920",
        "article_title": "oracle和mysql的区别",
        "comment_count": "1",
        "favor_count": "16",
        "nick_name": f"奋豆来袭{uuid.uuid4()}",
    },
    {
        "article_detail_url": "https://blog.csdn.net/Saintmm/article/details/129470532",
        "article_title": "Spring MVC自定义类型转换器Converter、参数解析器HandlerMethodArgumentResolver",
        "comment_count": "11",
        "favor_count": "16",
        "nick_name": f"秃秃爱健身{uuid.uuid4()}",
    },
    {
        "article_detail_url": "test_data",
        "article_title": "test_data",
        "comment_count": "test_data",
        "favor_count": "test_data",
        "nick_name": f"秃秃爱健身{uuid.uuid4()}",
    },
]


@pytest.fixture(scope="module")
def mongodb_first_step(mongodb_conn):
    # 前提准备，先创建需要的数据库集合的测试数据
    with open(
        f"{tests_dir}/docs/json/_test_article_info_table.json", "r", encoding="utf-8"
    ) as f:
        mongodb_data = json.load(f)
    save_data = mongodb_data["RECORDS"]
    mongodb_conn[mongodb_database][test_table].drop()
    mongodb_conn[mongodb_database][test_table].insert_many(save_data)


def test_uri_connect(mongodb_first_step):
    """测试 mongoDB 的 uri 链接方式"""
    mongodb = MongoDbBase(**mongodb_ori)
    select_res = mongodb.find(test_table, {"nick_name": "菜只因C"})
    print("select_res:", list(select_res))
    print("select_res:", select_res.count())
    assert select_res.count() >= 1


def test_key_connect():
    """测试 mongoDB 的 key 关键字链接方式"""
    mongodb_ori["connect_style"] = "K"
    mongodb = MongoDbBase(**mongodb_ori)
    select_res = mongodb.find(test_table, {"nick_name": "菜只因C"})
    print("select_res:", list(select_res), select_res.count())
    assert select_res.count() >= 1


def test_auth_connect():
    """测试 mongoDB 的 auth 认证链接方式 (pymongo 3.11.0 及以下版本使用)"""
    mongodb_ori["connect_style"] = "A"
    mongodb = MongoDbBase(**mongodb_ori)
    select_res = mongodb.find(test_table, {"nick_name": "菜只因C"})
    print("select_res:", list(select_res))
    assert select_res.count() >= 1


def test_insert_one():
    """测试 mongoDB 插入一条数据"""
    mongodb = MongoDbBase(**mongodb_ori)
    insert_id = mongodb.insert_one(
        test_table,
        add_data_list[0],
    )
    print("insert_id:", insert_id)
    assert insert_id is not None


def test_insert_many():
    """测试 mongoDB 插入多条数据"""
    mongodb = MongoDbBase(**mongodb_ori)
    insert_res = mongodb.insert_many(
        test_table,
        add_data_list[1:],
    )
    print(insert_res, type(insert_res))
    assert len(insert_res) == 2


def test_update():
    """测试 mongoDB 更新数据"""
    mongodb = MongoDbBase(**mongodb_ori)
    update_res = mongodb.update_super(
        collection=test_table,
        select_dict={
            "article_title": "蓝桥杯第十四届蓝桥杯模拟赛第三期考场应对攻略（C/C++）",
            "nick_name": "菜只因C",
        },
        set_dict={"favor_count": "500"},
    )
    print("update_res:", update_res)
    assert update_res >= 0


def test_delete():
    """测试 mongoDB 删除数据"""
    mongodb = MongoDbBase(**mongodb_ori)
    delete_res = mongodb.delete(
        test_table, {"article_title": {"$regex": "蓝桥杯第十四届蓝桥杯模拟赛第三期考场应对攻略"}}
    )
    print("delete_res:", delete_res)
    assert delete_res >= 0


def test_find():
    """测试 mongoDB 查询数据"""
    mongodb = MongoDbBase(**mongodb_ori)
    select_res = mongodb.find(test_table, {"favor_count": "46"}).count()
    print("select_res:", select_res)
    assert select_res >= 1

    select_res = list(
        mongodb.find(
            test_table,
            {"nick_name": {"$exists": True}},
            {"article_title": 1, "nick_name": 1, "favor_count": 1, "_id": 0},
        )
        .limit(2)
        .skip(1)
    )
    print("select_res:", select_res)
    assert len(select_res) == 2, (
        select_res[0]["article_title"] == "出道即封神的ChatGPT，现在怎么样了？"
    )


def test_upload():
    """测试 mongoDB 上传图片方法"""
    import requests

    mongodb = MongoDbBase(**mongodb_ori)
    r = requests.get(url="https://static.jzmbti.com/ceshi/qn/1002.png")
    content_type = dict(r.headers)["Content-Type"]
    print("图片的类型 content_type 为:", content_type)
    # 返回上传后的 ID 及图片链接
    mongo_upload_id, image_id = mongodb.upload(
        file_name="test2.jpg",
        _id="121212121213",
        content_type=content_type,
        collection="fs",
        file_data=r.content,
    )
    assert mongo_upload_id is not None, image_id is not None
