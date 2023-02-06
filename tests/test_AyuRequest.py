from ayugespidertools.AyuRequest import AiohttpRequest


def callback_tmp(response):
    print(response.text)


def test_aiohttp_reqeust():
    r = AiohttpRequest(
        url="https://www.baidu.com",
        callback=callback_tmp,
        method="GET",
        headers={
            "USER_AGENT": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3100.0 Safari/537.36",
        },
        cookies={"name": "ayuge"},
        meta={
            "curr_page": 1,
        },
    )
    print(r)
    assert r is not None
