from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.items import DataItem


def test_judge_str_is_json():
    data = '{"post_key1": post_value1}'
    res = ReuseOperation.judge_str_is_json(judge_str=data)
    print(res)
    data = '{"post_key1": "post_value1"}'
    res1 = ReuseOperation.judge_str_is_json(judge_str=data)
    print(res1)
    data = "post_key1=post_value1"
    res2 = ReuseOperation.judge_str_is_json(judge_str=data)
    print(res2)
    assert all([res is False, res1 is True, res2 is False])


def test_get_items_except_keys():
    dict_conf = {
        "alldata": {
            "article_title": DataItem("如何使用JavaMailSender给曾经心爱的她发送一封特别的邮件", "文章标题"),
            "comment_count": DataItem("69", "文章评论数量"),
            "favor_count": DataItem("41", "文章赞成数量"),
            "nick_name": DataItem("Binaire", "文章作者昵称"),
        },
        "table": "article_info_list",
        "item_mode": "Mysql",
    }
    res = ReuseOperation.get_items_except_keys(
        dict_conf=dict_conf, keys=["table", "item_mode"]
    )
    print("res:", res)
    assert list(res.keys()) == ["alldata"]


def test_is_dict_meet_min_limit():
    judge_dict = {"user": "admin", "age": 18, "height": 170}
    res = ReuseOperation.is_dict_meet_min_limit(
        dict_conf=judge_dict,
        key_list=["user", "age"],
    )
    res2 = ReuseOperation.is_dict_meet_min_limit(
        dict_conf=judge_dict,
        key_list=["user", "address"],
    )
    assert all([res is True, res2 is False])


def test_get_ck_dict_from_headers():
    ck_str = (
        "__gads=ID=5667bf1cc1623793:T=1656574796:RT=1656574796:S=ALNI_"
        "MYD2F7TGXOAaJFaIjtXL1pKiz8IwQ; _gid=GA1.2.1261442913.1661823137; _ga_5RS2C633VL"
        "=GS1.1.1661912227.10.0.1661912227.0.0.0; _ga=GA1.1.1076553851.1656574796; __gpi="
        "UID=000007372209e6e0:T=1656574796:RT=1661912226:S=ALNI_MZkxoWl7cZYRkWzt2WKaxXQ7b47xw"
    )
    res = ReuseOperation.get_ck_dict_from_headers(headers_ck_str=ck_str)
    print("ck_dict_res:", res, type(res))
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
    print("res:", res)
    assert res == {
        "NAME": "John",
        "ADDRESS": {"CITY": "New York", "STATE": "NY"},
        "PHONE": {"HOME": "QWER", "WORK": "WASD"},
        2: {22: "aaa", "WORK": "ABC", "THIRD": {"A": 1, "B": 2}},
    }


def test_get_req_dict_from_scrapy():
    scrapy_body_str = "post_key1=post_value1&post_key2=post_value2"

    res = ReuseOperation.get_req_dict_from_scrapy(req_body_data_str=scrapy_body_str)
    print("req body dict:", res)
    assert res == {"post_key1": "post_value1", "post_key2": "post_value2"}


def test_get_array_depth():
    array = ["a", "b"]
    array_two = ["a", [1, [2, [3, 4]]], ["b", "c"]]
    array_three = ["a", (1, [2, [3, 4]]), ["b", "c"]]
    len1 = ReuseOperation.get_array_depth(array=array)
    print("len1:", len1)
    len2 = ReuseOperation.get_array_depth(array=array_two)
    print("len2:", len2)
    len3 = ReuseOperation.get_array_depth(array=array_three)
    print("len3:", len3)
    assert all([len1 == 1, len2 == 4, len3 == 4])
