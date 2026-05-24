import warnings

from scrapy.http import Headers

from ayugespidertools import AiohttpRequest


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

    aiohttp_args = copied.meta["aiohttp"]["args"]
    assert isinstance(copied, AiohttpRequest)
    assert isinstance(copied.headers, Headers)
    assert aiohttp_args["headers"] == headers
    assert not isinstance(aiohttp_args["headers"], Headers)
    assert aiohttp_args["cookies"] == {"ck": "value"}
    assert copied.meta["meta_data"] == "test"
    assert copied.cb_kwargs == {"request_name": 1}
    assert copied.dont_filter is True
