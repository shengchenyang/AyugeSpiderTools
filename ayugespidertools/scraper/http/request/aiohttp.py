from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Self, cast

from scrapy import Request

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import _SENTINEL, URL, sentinel
from ayugespidertools.exceptions import AyugeSpiderToolsDeprecationWarning

__all__ = [
    "AiohttpRequest",
]

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Sequence
    from ssl import SSLContext
    from typing import Concatenate

    from aiohttp.client import ClientTimeout
    from aiohttp.client_middlewares import ClientMiddlewareType
    from aiohttp.client_reqrep import ClientResponse, Fingerprint, UploadTracker
    from aiohttp.helpers import BasicAuth
    from aiohttp.typedefs import LooseCookies, LooseHeaders, Query
    from scrapy.http import Response
    from twisted.python.failure import Failure

    from ayugespidertools.common.typevars import (
        ScrapyCookiesT,
        ScrapyHeadersT,
        StrOrURL,
    )

    CallbackT = Callable[Concatenate[Response, ...], Any]


class AiohttpRequest(Request):
    __slots__ = ("_ayuge_aiohttp_args",)

    def __init__(
        self,
        url: StrOrURL,
        callback: CallbackT | None = None,
        method: str = "GET",
        headers: LooseHeaders | ScrapyHeadersT | None = None,
        body: _SENTINEL = sentinel,
        cookies: LooseCookies | ScrapyCookiesT | None = None,
        meta: dict[str, Any] | None = None,
        encoding: str = "utf-8",
        priority: int = 0,
        dont_filter: bool = False,
        errback: Callable[[Failure], Any] | None = None,
        flags: list[str] | None = None,
        cb_kwargs: dict[str, Any] | None = None,
        parent_id: int | None = None,
        params: Query = None,
        data: Any = None,
        json: Any = None,
        skip_auto_headers: Iterable[str] | None = None,
        auth: BasicAuth | None = None,
        allow_redirects: bool | None = None,
        max_redirects: int | None = None,
        compress: str | bool | None = None,
        chunked: bool | None = None,
        expect100: bool | None = None,
        raise_for_status: (
            None | bool | Callable[[ClientResponse], Awaitable[None]]
        ) = None,
        read_until_eof: bool | None = None,
        proxy: StrOrURL | None = None,
        proxy_auth: BasicAuth | None = None,
        timeout: ClientTimeout | None = None,
        verify_ssl: bool | None = None,
        fingerprint: bytes | None = None,
        ssl_context: SSLContext | None = None,
        ssl: SSLContext | bool | Fingerprint = True,
        server_hostname: str | None = None,
        proxy_headers: LooseHeaders | None = None,
        trace_request_ctx: object = None,
        read_bufsize: int | None = None,
        auto_decompress: bool | None = None,
        max_line_size: int | None = None,
        max_field_size: int | None = None,
        max_headers: int | None = None,
        middlewares: Sequence[ClientMiddlewareType] | None = None,
        upload_tracker: UploadTracker | None = None,
        **kwargs: Any,
    ) -> None:
        if body is not sentinel:
            warnings.warn(
                "parameter 'body' is deprecated, use 'json' or 'data' argument instead",
                category=AyugeSpiderToolsDeprecationWarning,
                stacklevel=2,
            )

        aiohttp_req_args = {
            "method": method,
            "url": url,
            "params": params,
            "data": data,
            "json": json,
            "cookies": cookies,
            "headers": headers,
            "skip_auto_headers": skip_auto_headers,
            "auth": auth,
            "allow_redirects": allow_redirects,
            "max_redirects": max_redirects,
            "compress": compress,
            "chunked": chunked,
            "expect100": expect100,
            "raise_for_status": raise_for_status,
            "read_until_eof": read_until_eof,
            "proxy": proxy,
            "proxy_auth": proxy_auth,
            "timeout": timeout,
            "verify_ssl": verify_ssl,
            "fingerprint": fingerprint,
            "ssl_context": ssl_context,
            "ssl": ssl,
            "server_hostname": server_hostname,
            "proxy_headers": proxy_headers,
            "trace_request_ctx": trace_request_ctx,
            "read_bufsize": read_bufsize,
            "auto_decompress": auto_decompress,
            "max_line_size": max_line_size,
            "max_field_size": max_field_size,
            "max_headers": max_headers,
            "middlewares": middlewares,
            "upload_tracker": upload_tracker,
        }
        if kwargs:
            aiohttp_req_args.update(kwargs)
        aiohttp_req_args = ReuseOperation.filter_none_value(aiohttp_req_args)
        self._ayuge_aiohttp_args = aiohttp_req_args

        if isinstance(url, URL):
            url = str(url)

        super().__init__(
            url=url,
            callback=callback,
            method=method,
            headers=cast("ScrapyHeadersT", headers),
            cookies=cast("ScrapyCookiesT", cookies),
            meta=meta,
            encoding=encoding,
            priority=priority,
            dont_filter=dont_filter,
            errback=errback,
            flags=flags,
            cb_kwargs=cb_kwargs,
            parent_id=parent_id,
        )

    def copy(self) -> Self:
        return self.__class__(
            callback=self.callback,
            meta=self.meta,
            encoding=self.encoding,
            priority=self.priority,
            dont_filter=self.dont_filter,
            errback=self.errback,
            flags=self.flags,
            cb_kwargs=self.cb_kwargs,
            parent_id=self.id,
            **self._ayuge_aiohttp_args,
        )
