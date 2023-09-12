import copy
from dataclasses import asdict
from typing import Callable, List, Optional, Union

from scrapy import Request

from ayugespidertools.common.typevars import AiohttpRequestArgs

__all__ = [
    "AiohttpRequest",
]


class AiohttpRequest(Request):
    """为 scrapy 的 Request 对象添加额外的参数"""

    def __init__(
        self,
        url: str,
        callback: Optional[Callable] = None,
        method: str = "GET",
        headers: Optional[dict] = None,
        body: Optional[Union[bytes, str]] = None,
        cookies: Optional[Union[dict, List[dict]]] = None,
        meta: Optional[dict] = None,
        args: Optional[Union[AiohttpRequestArgs, dict]] = None,
        **kwargs,
    ) -> None:
        # 用 meta 缓存 scrapy meta 的参数
        meta = copy.deepcopy(meta) or {}
        aiohttp_meta = meta.setdefault("aiohttp", {})

        _args = {"url": url}
        if isinstance(args, AiohttpRequestArgs):
            args = asdict(args)
        _args.update(args or {})
        _args.update(aiohttp_meta.get("args", {}))
        aiohttp_meta["args"] = _args

        super(AiohttpRequest, self).__init__(
            url,
            callback,
            method=method,
            headers=headers,
            body=body,
            cookies=cookies,
            meta=meta,
            **kwargs,
        )
