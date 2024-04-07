import copy
import json
import uuid
from pathlib import Path

import pytest

from ayugespidertools.mongoclient import MongoDbBase, MongoDBEngineClass
from tests import MONGODB_CONFIG, tests_dir
from tests.conftest import mongodb_database, test_table

mongodb_uri = MONGODB_CONFIG["uri"]

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
    _mongo_file = Path(tests_dir, "docs/json/_test_article_info_table.json")
    mongodb_data = json.loads(_mongo_file.read_text(encoding="utf-8"))
    save_data = mongodb_data["RECORDS"]
    mongodb_conn[mongodb_database][test_table].drop()
    mongodb_conn[mongodb_database][test_table].insert_many(save_data)


def test_key_connect(mongodb_first_step):
    """测试 mongoDB 的 key 链接方式"""
    _mongo_conf = copy.deepcopy(MONGODB_CONFIG)
    _mongo_conf.pop("uri")
    conn, db = MongoDbBase.connects(**_mongo_conf)
    select_res = db[test_table].find({"nick_name": "菜只因C"})
    assert select_res.count() >= 1


def test_uri_connect():
    """测试 mongoDB 的 uri 关键字链接方式"""
    conn, db = MongoDbBase.connects(uri=mongodb_uri)
    select_res = db[test_table].find({"nick_name": "菜只因C"})
    assert select_res.count() >= 1


def test_insert_one():
    """测试 mongoDB 插入一条数据"""
    conn, db = MongoDBEngineClass(engine_url=mongodb_uri).engine
    insert_res = db[test_table].insert_one(
        add_data_list[0],
    )
    assert insert_res.inserted_id is not None


def test_insert_many():
    """测试 mongoDB 插入多条数据"""
    conn, db = MongoDBEngineClass(engine_url=mongodb_uri).engine
    insert_res = db[test_table].insert_many(
        add_data_list[1:],
    )
    assert len(insert_res.inserted_ids) == 2


def test_update_one():
    """测试 mongoDB 更新数据"""
    conn, db = MongoDBEngineClass(engine_url=mongodb_uri).engine
    select_dict = {
        "article_title": "蓝桥杯第十四届蓝桥杯模拟赛第三期考场应对攻略（C/C++）",
        "nick_name": "菜只因C",
    }
    set_dict = {"favor_count": "500"}
    update_res = db[test_table].update_one(select_dict, {"$set": set_dict})
    assert update_res.modified_count >= 0


def test_delete():
    """测试 mongoDB 删除数据"""
    conn, db = MongoDBEngineClass(engine_url=mongodb_uri).engine
    delete_res = db[test_table].delete_many(
        filter={
            "article_title": {"$regex": "蓝桥杯第十四届蓝桥杯模拟赛第三期考场应对攻略"}
        }
    )
    assert delete_res.deleted_count >= 0


def test_find():
    """测试 mongoDB 查询数据"""
    conn, db = MongoDBEngineClass(engine_url=mongodb_uri).engine
    select_res = db[test_table].find({"favor_count": "46"}).count()
    assert select_res >= 1

    select_res = list(
        db[test_table]
        .find(
            {"nick_name": {"$exists": True}},
            {"article_title": 1, "nick_name": 1, "favor_count": 1, "_id": 0},
        )
        .limit(2)
        .skip(1)
    )
    assert len(select_res) == 2, (
        select_res[0]["article_title"] == "出道即封神的ChatGPT，现在怎么样了？"
    )


def test_upload():
    """测试 mongoDB 上传图片方法"""
    conn, db = MongoDBEngineClass(engine_url=mongodb_uri).engine
    png_bytes = Path(tests_dir, "docs/image/mongo_upload.png").read_bytes()

    # 返回上传后的 ID 及图片链接
    mongo_upload_id, image_id = MongoDbBase.upload(
        db=db,
        file_name="test2.jpg",
        _id="121212121213",
        content_type="image/png",
        collection="fs",
        file_data=png_bytes,
    )
    assert mongo_upload_id is not None, image_id is not None
