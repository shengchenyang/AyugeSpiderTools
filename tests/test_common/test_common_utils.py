import json
from pathlib import Path

import pytest
from scrapy.http.request import Request
from scrapy.http.response.text import TextResponse

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.extras.cvnpil import BezierTrajectory
from tests import CONSUL_CONFIG, tests_dir

json_data_example = {
    "code": "0",
    "message": "success",
    "data": {
        "thumb_up": 0,
        "im": 33,
        "gitChat_thumb_up": 0,
        "avatarUrl": "https://profile.csdnimg.cn/D/6/8/2_Ayuge2",
        "invitation": 0,
        "gitChat_system": 0,
        "GlobalSwitch": {
            "private_message_who_follows_me": True,
            "email_commit_receive": True,
            "interactive_follow": True,
            "email_collect_receive": True,
            "system_digital": True,
            "private_message_stranger": True,
            "email_support_receive": True,
            "interactive_like": True,
            "interactive_comment_digital": True,
            "system": True,
            "interactive_like_digital": True,
            "interactive_follow_digital": True,
            "email_follow_receive": True,
            "interactive_comment": True,
            "private_message_who_me_follows": True,
            "announcement_digital": True,
            "email": True,
            "announcement": True,
        },
        "edu_thumb_up": 0,
        "blink_thumb_up": 0,
        "follow": 0,
        "totalCount": 34,
        "coupon_order": 0,
        "edu_comment": 0,
        "edu_system": 0,
        "system": 1,
        "comment": 0,
        "blink_comment": 0,
        "gitChat_comment": 0,
        "my_add_list": [],
        "my_add_dict": {},
    },
    "status": True,
}

body = Path(tests_dir, "docs/txt/baidu_pagesource.html").read_text(encoding="utf-8")
_response = TextResponse(url="https://top.baidu.com", body=body, encoding="utf-8")


def test_get_remote_kvs():
    res = ToolsForAyu.get_remote_kvs(
        url=CONSUL_CONFIG["url"],
    )
    _res = json.loads(res)
    _res_lower = ReuseOperation.dict_keys_to_lower(_res)
    assert _res_lower.get("mysql") is not None, _res_lower.get("mongodb") is not None


def test_fetch_remote_conf():
    res = ToolsForAyu.fetch_remote_conf(
        conf_name="mysql",
        url=CONSUL_CONFIG["url"],
        format="json",
    )
    assert res.get("host") is not None, res.get("port") is not None


def test_extract_with_css():
    content_type = ToolsForAyu.extract_with_css(
        response=_response,
        query="div.side-title_1wfo5.c-theme-color::text",
    )
    assert content_type == "热搜榜"
    title_lst = ToolsForAyu.extract_with_css(
        response=_response,
        query="div.c-single-text-ellipsis::text",
        get_all=True,
    )
    assert len(title_lst) == 31
    no_div_element = ToolsForAyu.extract_with_css(
        response=_response,
        query="div.no-this-div::text",
    )
    assert no_div_element == ""
    no_div_element_lst = ToolsForAyu.extract_with_css(
        response=_response,
        query="div.no-this-div::text",
        get_all=True,
    )
    assert no_div_element_lst == []


def test_extract_with_xpath():
    content_type = ToolsForAyu.extract_with_xpath(
        response=_response,
        query="//div[@class='side-title_1wfo5 c-theme-color']/text()",
    )
    assert content_type == "热搜榜"
    title_lst = ToolsForAyu.extract_with_xpath(
        response=_response,
        query="//div[@class='c-single-text-ellipsis']/text()",
        get_all=True,
    )
    assert len(title_lst) == 31
    no_div_element = ToolsForAyu.extract_with_xpath(
        response=_response,
        query="//div[@class='no-this-div']/text()",
    )
    assert no_div_element == ""
    no_div_element_lst = ToolsForAyu.extract_with_xpath(
        response=_response,
        query="//div[@class='no-this-div']/text()",
        get_all=True,
    )
    assert no_div_element_lst == []


def test_extract_with_json():
    res = ToolsForAyu.extract_with_json(
        json_data=json_data_example, query=["data", "im"]
    )
    assert res == "33", isinstance(res, str)

    # 取不存在的字段时
    res = ToolsForAyu.extract_with_json(
        json_data=json_data_example, query=["data", "GlobalSwitch", "announcement_ayu"]
    )
    assert res == ""

    res = ToolsForAyu.extract_with_json(
        json_data=json_data_example, query=["data", "my_add_list"]
    )
    assert res == []

    res = ToolsForAyu.extract_with_json(
        json_data=json_data_example, query=["data", "my_add_dict"]
    )
    assert res == {}


def test_extract_with_json_rules():
    res = ToolsForAyu.extract_with_json_rules(
        json_data=json_data_example, query_rules=[["data", "im"]]
    )
    assert res == "33", isinstance(res, str)

    # 参数层级大于 2 时，会报错
    with pytest.raises(AssertionError) as _assertion_err:
        ToolsForAyu.extract_with_json_rules(
            json_data=json_data_example, query_rules=[[["depth_to_big"], "data", "im"]]
        )
    assert (
        str(_assertion_err.value) == "query_rules 参数错误，请输入深度最多为 2 的参数！"
    )

    res2 = ToolsForAyu.extract_with_json_rules(
        json_data=json_data_example, query_rules=[["data", "yy"], "message"]
    )
    assert res2 == "success"

    # 当 json 字段的值为 int, float, str, complex 或 list 等没有 get 方法的时候
    with pytest.raises(AttributeError) as _attribute_err:
        ToolsForAyu.extract_with_json_rules(
            json_data=json_data_example, query_rules=[["data", "im", "cc"], "message"]
        )
    assert str(_attribute_err.value) == "'int' object has no attribute 'get'"


def test_first_not_none():
    data_lst = [None, "", False, "data"]
    res = ToolsForAyu.first_not_none(data_lst)
    assert res == ""


def test_get_dict_form_scrapy_req_headers():
    _headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }
    scrapy_headers = Request(url="https://www.baidu.com", headers=_headers).headers
    res = ToolsForAyu.get_dict_form_scrapy_req_headers(scrapy_headers=scrapy_headers)
    assert res == _headers


def test_bezier_track():
    """测试贝塞尔曲线生成轨迹方法"""
    a = BezierTrajectory()
    res = a.gen_track(start=[50, 268], end=[367, 485], num=45, order=4, mode=2)
    track = res["trackArray"]
    print(track)
    x_lst = []
    y_lst = []
    for i in res["trackArray"]:
        x_lst.append(i[0])
        y_lst.append(i[1])
    print("x_lst:", x_lst)
    print("y_lst:", y_lst)
    assert all(
        [
            len(x_lst) == len(y_lst) == 45,
            int(x_lst[0]) == 50,
            int(y_lst[0]) == 268,
            int(x_lst[-1]) == 367,
            int(y_lst[-1]) == 485,
        ]
    )


def test_gen_selenium_track():
    tracks = ToolsForAyu.gen_selenium_track(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_gen_tracks():
    tracks = ToolsForAyu.gen_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks
