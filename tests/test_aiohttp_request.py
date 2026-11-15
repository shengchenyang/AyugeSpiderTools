import warnings

from scrapy.http import Headers

from ayugespidertools import AiohttpRequest, CurlCffiRequest


def test_custom_requests_do_not_create_instance_dict():
    assert not hasattr(AiohttpRequest("https://example.com"), "__dict__")
    assert not hasattr(CurlCffiRequest("https://example.com"), "__dict__")


def test_aiohttp_request_copy_keeps_aiohttp_args():
    headers = {"Cookie": "a=b"}
    request = AiohttpRequest(
        url="https://example.com/get",
        headers=headers,
        cookies={"ck": "value"},
        meta={"meta_data": "test"},
        cb_kwargs={"request_name": 1},
        dont_filter=True,
    )

    with warnings.catch_warnings(record=False):
        warnings.simplefilter("error")
        copied = request.copy()

    aiohttp_args = request._ayuge_aiohttp_args
    assert isinstance(copied, AiohttpRequest)
    assert isinstance(copied.headers, Headers)
    assert aiohttp_args["headers"] == headers
    assert not isinstance(aiohttp_args["headers"], Headers)
    assert aiohttp_args["cookies"] == {"ck": "value"}
    assert copied.meta["meta_data"] == "test"
    assert copied.cb_kwargs == {"request_name": 1}
    assert copied.dont_filter is True


def test_aiohttp_314_request_args_are_preserved():
    request = AiohttpRequest(
        "https://example.com",
        params={"page": 1},
        compress=True,
        max_headers=64,
        middlewares=(),
    )

    args = request._ayuge_aiohttp_args
    assert args["params"] == {"page": 1}
    assert args["compress"] is True
    assert args["max_headers"] == 64
    assert args["middlewares"] == ()
