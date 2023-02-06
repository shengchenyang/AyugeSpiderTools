import copy
from typing import Callable, List, Optional, Union

from scrapy import Request

from ayugespidertools.common.Params import Param

__all__ = [
    "AiohttpRequest",
]


class AiohttpRequest(Request):
    """
    为 scrapy 的 Request 对象添加额外的参数
    """

    def __init__(
        self,
        url: str,
        callback: Optional[Callable] = None,
        method: str = "GET",
        headers: Optional[dict] = None,
        body: Optional[Union[bytes, str]] = None,
        cookies: Optional[Union[dict, List[dict]]] = None,
        meta: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> None:
        # 用 meta 缓存 scrapy meta 的参数
        meta = copy.deepcopy(meta) or {}
        aiohttp_meta = meta.get("aiohttp_args") or {}

        # TODO: 可添加和修改默认参数的值，后续可以在此完善功能
        self.proxy = aiohttp_meta.get("proxy", {"http:": "http://10.10.10.10:10000"})
        self.timeout = aiohttp_meta.get("timeout", Param.aiohttp_req_timeout)
        self.sleep = aiohttp_meta.get("sleep", None)

        aiohttp_meta = meta.setdefault("aiohttp_args", {})
        aiohttp_meta["proxy"] = self.proxy
        aiohttp_meta["timeout"] = self.timeout
        super(AiohttpRequest, self).__init__(
            url,
            callback,
            method=method,
            headers=headers,
            body=body,
            cookies=cookies,
            meta=meta,
            *args,
            **kwargs,
        )
