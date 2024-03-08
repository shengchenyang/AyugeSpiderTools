from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Optional, Tuple, Union

from scrapy import FormRequest

from ayugespidertools.scraper.http.request import AiohttpRequest

__all__ = [
    "AiohttpFormRequest",
]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import AiohttpRequestArgs

FormdataKVType = Tuple[str, Union[str, Iterable[str]]]
FormdataType = Optional[Union[dict, List[FormdataKVType]]]


class AiohttpFormRequest(AiohttpRequest, FormRequest):
    """使用 aiohttp 发送 FormRequest 请求"""

    def __init__(
        self,
        url: Optional[str] = None,
        callback: Optional[Callable] = None,
        method: Optional[str] = None,
        formdata: FormdataType = None,
        body: Optional[Union[bytes, str]] = None,
        args: Optional[Union["AiohttpRequestArgs", dict]] = None,
        **kwargs: Any
    ) -> None:
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
