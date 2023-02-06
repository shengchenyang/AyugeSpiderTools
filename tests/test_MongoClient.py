from bson.objectid import ObjectId

from ayugespidertools.config import NormalConfig
from ayugespidertools.MongoClient import MongoDbBase

# mongoDB 链接配置信息
MONGODB_CONFIG = NormalConfig.MONGODB_CONFIG


def test_uri_connect():
    """测试 mongoDB 的 uri 链接方式"""
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    print("MONGODB_CONFIG:", MONGODB_CONFIG)
    print("mongodb.connect:", mongodb.conn)
    print("mongodb.db:", mongodb.db)
    select_res = mongodb.find("book_info_list", {"book_name": "武帝独尊"})
    print("select_res:", list(select_res))
    assert mongodb is not None


def test_key_connect():
    """测试 mongoDB 的 key 关键字链接方式"""
    MONGODB_CONFIG["connect_style"] = "K"
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    select_res = mongodb.find("title", {"name": "标题名称3"}).count()
    print("select_res:", select_res)
    assert mongodb is not None


def test_auth_connect():
    """测试 mongoDB 的 auth 认证链接方式 (pymongo 3.11.0 及以下版本使用)"""
    MONGODB_CONFIG["connect_style"] = "A"
    print(MONGODB_CONFIG)
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    select_res = mongodb.find("title", {"name": "标题名称3"}).count()
    print("select_res:", select_res)
    assert mongodb is not None


def test_insert_one():
    """测试 mongoDB 插入一条数据"""
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    insert_res = mongodb.insert_one(
        "test", {"name": "标题名称", "addtime": "2020-07-25", "adduser": "mine"}
    )
    print(insert_res, type(insert_res))
    assert insert_res is not None


def test_insert_many():
    """测试 mongoDB 插入多条数据"""
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    insert_res = mongodb.insert_many(
        "title",
        [
            {"name": "标题名称3", "addtime": "2020-07-25", "adduser": "mine3"},
            {"name": "标题名称2", "addtime": "2020-07-25", "adduser": "mine2"},
        ],
    )
    print(insert_res, type(insert_res))
    assert insert_res is not None


def test_update():
    """测试 mongoDB 更新数据"""
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    update_res = mongodb.update_super(
        collection="title", select_dict={"name": "标题名称32"}, set_dict={"name": "标题名称3"}
    )
    print("update_res:", update_res)
    assert update_res is not None


def test_delete():
    """测试 mongoDB 删除数据"""
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    delete_res = mongodb.delete("title", {"name": {"$regex": "标题名称3"}})
    print("delete_res:", delete_res)
    assert delete_res is not None


def test_find():
    """测试 mongoDB 查询数据"""
    mongodb = MongoDbBase(**MONGODB_CONFIG)
    select_res = mongodb.find("title", {"name": "标题名称3"}).count()
    print("select_res:", select_res)
    select_res = list(
        mongodb.find(
            "title", {"name": {"$exists": True}}, {"name": 1, "addtime": 1, "_id": 0}
        )
        .limit(5)
        .skip(2)
    )
    print("select_res:", select_res)
    select_res = list(
        mongodb.find(
            "title",
            {"_id": ObjectId("62de112a907ce5580321e1bd")},
            {"_id": 1, "name": 1},
        )
    )
    print("select_res:", select_res)
    assert 1


def test_upload():
    """测试 mongoDB 上传图片方法"""
    import requests

    mongodb = MongoDbBase(**MONGODB_CONFIG)
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
    print(mongo_upload_id, image_id)
