import copy
from typing import NamedTuple

import scrapy

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import AlterItemTable
from ayugespidertools.items import AyuItem, DataItem


class ScrapyTestItem(scrapy.Item):
    name = scrapy.Field()


scrapy_item = ScrapyTestItem(name="zhangsan")


def init_reshape_item(alert_item):
    item_dict = ReuseOperation.item_to_dict(alert_item)
    return ReuseOperation.reshape_item(item_dict)


def test_item_to_dict():
    expect_res = {"name": "zhangsan"}
    item_dict = copy.deepcopy(expect_res)
    res = ReuseOperation.item_to_dict(item_dict)
    assert isinstance(res, dict), res == expect_res

    res = ReuseOperation.item_to_dict(scrapy_item)
    assert isinstance(res, dict), res == expect_res

    ayu_item = AyuItem(_table="t", name="zhangsan")
    res = ReuseOperation.item_to_dict(ayu_item)
    assert isinstance(res, dict), res == {"name": "zhangsan", "_table": "t"}


def test_reshape_item():
    article_item = AyuItem(
        url=DataItem("u", "详情链接"),
        name=DataItem("n", "作者昵称"),
        _table=DataItem("t", "文章信息表"),
    )
    res = init_reshape_item(article_item)

    _expect_new_item = {"url": "u", "name": "n"}
    _expect_notes_dic = {"name": "作者昵称", "url": "详情链接"}
    _expect_notes_dic_sec = {"name": "", "url": ""}
    _expect_table = AlterItemTable(name="t", notes="")
    assert all(
        [
            res.new_item == _expect_new_item,
            res.notes_dic == _expect_notes_dic,
            res.table == AlterItemTable(name="t", notes="文章信息表"),
        ]
    )

    article_item_sec = AyuItem(url="u", name="n", _table="t")
    res = init_reshape_item(article_item_sec)
    assert all(
        [
            res.new_item == _expect_new_item,
            res.notes_dic == _expect_notes_dic_sec,
            res.table == _expect_table,
        ]
    )

    article_item_third = {"url": "u", "name": "n", "_table": "t"}
    res = init_reshape_item(article_item_third)
    assert all(
        [
            res.new_item == _expect_new_item,
            res.notes_dic == _expect_notes_dic_sec,
            res.table == _expect_table,
        ]
    )

    class ScrapyTestItem(scrapy.Item):
        url = scrapy.Field()
        name = scrapy.Field()
        _table = scrapy.Field()

    article_item_fourth = ScrapyTestItem(url="u", name="n", _table="t")
    res = init_reshape_item(article_item_fourth)
    assert all(
        [
            res.new_item == _expect_new_item,
            res.notes_dic == _expect_notes_dic_sec,
            res.table == _expect_table,
        ]
    )


def test_is_namedtuple_instance():
    class Demo(NamedTuple):
        host: str
        port: int

    demo = Demo(host="localhost", port=1234)
    res = ReuseOperation.is_namedtuple_instance(demo)
    assert res is True

    res = ReuseOperation.is_namedtuple_instance({"a": 2})
    assert res is False

    res = ReuseOperation.is_namedtuple_instance(scrapy_item)
    assert res is False


def test_random_weight():
    weight_data = [
        {"username": "xxx", "password": "***", "weight": 3},
        {"username": "YYY", "password": "---", "weight": 1},
    ]
    res = [ReuseOperation.random_weight(weight_data) for _ in range(40)]
    x_count = len([x for x in res if x["username"] == "xxx"])
    assert any([True, 20 < x_count < 40])


def test_judge_str_is_json():
    data = '{"post_key1": post_value1}'
    res = ReuseOperation.judge_str_is_json(judge_str=data)
    data = '{"post_key1": "post_value1"}'
    res1 = ReuseOperation.judge_str_is_json(judge_str=data)
    data = "post_key1=post_value1"
    res2 = ReuseOperation.judge_str_is_json(judge_str=data)
    res3 = ReuseOperation.judge_str_is_json(10)
    assert all([res is False, res1 is True, res2 is False, res3 is False])


def test_get_items_except_keys():
    dict_conf = {
        "alldata": {
            "article_title": DataItem(
                "如何使用JavaMailSender给曾经心爱的她发送一封特别的邮件", "文章标题"
            ),
            "comment_count": DataItem("69", "文章评论数量"),
            "favor_count": DataItem("41", "文章赞成数量"),
            "nick_name": DataItem("Binaire", "文章作者昵称"),
        },
        "table": "article_info_list",
        "item_mode": "Mysql",
    }
    res = ReuseOperation.get_items_except_keys(
        data=dict_conf, keys={"table", "item_mode"}
    )
    assert list(res.keys()) == ["alldata"], res["alldata"] == dict_conf["alldata"]


def test_is_dict_meet_min_limit():
    judge_dict = {"user": "admin", "age": 18, "height": 170}
    res = ReuseOperation.is_dict_meet_min_limit(
        data=judge_dict,
        keys={"user", "age"},
    )
    res2 = ReuseOperation.is_dict_meet_min_limit(
        data=judge_dict,
        keys={"user", "address"},
    )
    res3 = ReuseOperation.is_dict_meet_min_limit({}, ["user"])
    assert all([res is True, res2 is False, res3 is False])


def test_get_ck_dict_from_headers():
    ck_str = (
        "__gads=ID=5667bf1cc1623793:T=1656574796:RT=1656574796:S=ALNI_"
        "MYD2F7TGXOAaJFaIjtXL1pKiz8IwQ; _gid=GA1.2.1261442913.1661823137; _ga_5RS2C633VL"
        "=GS1.1.1661912227.10.0.1661912227.0.0.0; _ga=GA1.1.1076553851.1656574796; __gpi="
        "UID=000007372209e6e0:T=1656574796:RT=1661912226:S=ALNI_MZkxoWl7cZYRkWzt2WKaxXQ7b47xw"
    )
    res = ReuseOperation.get_ck_dict_from_headers(headers_ck_str=ck_str)
    assert res == {
        "__gads": "ID=5667bf1cc1623793:T=1656574796:RT=1656574796:S=ALNI_MYD2F7TGXOAaJFaIjtXL1pKiz8IwQ",
        "_gid": "GA1.2.1261442913.1661823137",
        "_ga_5RS2C633VL": "GS1.1.1661912227.10.0.1661912227.0.0.0",
        "_ga": "GA1.1.1076553851.1656574796",
        "__gpi": "UID=000007372209e6e0:T=1656574796:RT=1661912226:S=ALNI_MZkxoWl7cZYRkWzt2WKaxXQ7b47xw",
    }


def test_dict_keys_to_lower():
    ori_dict = {
        "Name": "John",
        "Address": {"City": "New York", "State": "NY"},
        "Phone": {"Home": "QWER", "Work": "WASD"},
        2: {22: "AAA", "Work": "ABC", "THIRD": {"A": 1, "B": 2}},
    }
    res = ReuseOperation.dict_keys_to_lower(deal_dict=ori_dict)
    assert res == {
        "name": "John",
        "address": {"city": "New York", "state": "NY"},
        "phone": {"home": "QWER", "work": "WASD"},
        2: {22: "AAA", "work": "ABC", "third": {"a": 1, "b": 2}},
    }


def test_dict_keys_to_upper():
    ori_dict = {
        "name": "John",
        "address": {"city": "New York", "state": "NY"},
        "Phone": {"home": "QWER", "work": "WASD"},
        2: {22: "aaa", "work": "ABC", "third": {"a": 1, "b": 2}},
    }
    res = ReuseOperation.dict_keys_to_upper(deal_dict=ori_dict)
    assert res == {
        "NAME": "John",
        "ADDRESS": {"CITY": "New York", "STATE": "NY"},
        "PHONE": {"HOME": "QWER", "WORK": "WASD"},
        2: {22: "aaa", "WORK": "ABC", "THIRD": {"A": 1, "B": 2}},
    }


def test_get_req_dict_from_scrapy():
    scrapy_body_str = "post_key1=post_value1&post_key2=post_value2"

    res = ReuseOperation.get_req_dict_from_scrapy(req_body_data_str=scrapy_body_str)
    assert res == {"post_key1": "post_value1", "post_key2": "post_value2"}


def test_get_array_depth():
    array_one = ["a", "b"]
    array_two = ["a", [1, [2, [3, 4]]], ["b", "c"]]
    array_three = ["a", (1, [2, [3, 4]]), ["b", "c"]]
    len1 = ReuseOperation.get_array_depth(array=array_one)
    len2 = ReuseOperation.get_array_depth(array=array_two)
    len3 = ReuseOperation.get_array_depth(array=array_three)
    assert all([len1 == 1, len2 == 4, len3 == 4])
