from ayugespidertools.request import AiohttpRequest


def callback_tmp(response):
    print(response.text)


def test_aiohttp_reqeust():
    _url = "https://www.baidu.com"
    _ua = "Opera/9.80 (X11; Linux i686|; Ubuntu/14.10) Presto/2.12.388 Version/12.16"
    _ck = {"name": "ayuge"}
    _meta = {
        "curr_page": 1,
    }
    r = AiohttpRequest(
        url=_url,
        callback=callback_tmp,
        method="GET",
        headers={
            "USER_AGENT": _ua,
        },
        cookies=_ck,
        meta=_meta,
    )
    assert all(
        [
            r.url == _url,
            r.method == "GET",
            r.headers["USER_AGENT"] == bytes(_ua, encoding="utf-8"),
            r.cookies == _ck,
            r.meta == {"curr_page": 1, "aiohttp": {"args": {"url": _url}}},
        ]
    )

    # todo: 添加具体应用场景及更详细的的测试用例。
