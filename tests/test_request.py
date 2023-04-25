from ayugespidertools.request import AiohttpRequest


def callback_tmp(response):
    print(response.text)


def test_aiohttp_reqeust():
    r = AiohttpRequest(
        url="https://www.baidu.com",
        callback=callback_tmp,
        method="GET",
        headers={
            "USER_AGENT": "Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16",
        },
        cookies={"name": "ayuge"},
        meta={
            "curr_page": 1,
        },
    )
    assert r is not None
