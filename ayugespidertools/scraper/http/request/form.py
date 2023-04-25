from typing import Union

from scrapy import FormRequest

from ayugespidertools.common.typevars import AiohttpRequestArgs
from ayugespidertools.scraper.http.request import AiohttpRequest

__all__ = [
    "AiohttpFormRequest",
]


class AiohttpFormRequest(AiohttpRequest, FormRequest):
    """
    使用 aiohttp 发送 FormRequest 请求
    """

    def __init__(
        self,
        url=None,
        callback=None,
        method=None,
        formdata=None,
        body=None,
        args: Union[AiohttpRequestArgs, dict] = None,
        **kwargs
    ):
        # First init FormRequest to get url, body and method
        if formdata:
            FormRequest.__init__(self, url=url, method=method, formdata=formdata)
            url, method, body = self.url, self.method, self.body
        # Then pass all other kwargs to AiohttpRequest
        AiohttpRequest.__init__(
            self,
            url=url,
            callback=callback,
            method=method,
            body=body,
            args=args,
            **kwargs
        )
