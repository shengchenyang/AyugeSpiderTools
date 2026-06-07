from __future__ import annotations

import copy
import warnings
from typing import TYPE_CHECKING, Any, cast

from scrapy import Request

from ayugespidertools.common.typevars import _SENTINEL, URL, sentinel
from ayugespidertools.exceptions import AyugeSpiderToolsDeprecationWarning

__all__ = [
    "CurlCffiRequest",
]

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from io import BytesIO
    from typing import Concatenate, Literal

    from curl_cffi import CurlMime
    from curl_cffi.const import CurlFollow, CurlHttpVersion
    from curl_cffi.requests import (
        BrowserTypeLiteral,
        CookieTypes,
        HeaderTypes,
        ProxySpec,
    )
    from curl_cffi.requests.impersonate import ExtraFingerprints, ExtraFpDict
    from curl_cffi.requests.session import HttpMethod, HttpVersionLiteral
    from scrapy.http import Response
    from twisted.python.failure import Failure

    from ayugespidertools.common.typevars import CookiesT, StrOrURL

    CallbackT = Callable[Concatenate[Response, ...], Any]
    ScrapyHeaders = Mapping[str, Any] | Iterable[tuple[str, Any]] | None
    ScrapyCookies = CookiesT | None


class CurlCffiRequest(Request):
    def __init__(
        self,
        url: StrOrURL,
        callback: CallbackT | None = None,
        method: HttpMethod = "GET",
        headers: HeaderTypes | None = None,
        body: _SENTINEL = sentinel,
        cookies: CookieTypes | None = None,
        meta: dict[str, Any] | None = None,
        encoding: str = "utf-8",
        priority: int = 0,
        dont_filter: bool = False,
        errback: Callable[[Failure], Any] | None = None,
        flags: list[str] | None = None,
        cb_kwargs: dict[str, Any] | None = None,
        params: dict | list | tuple | None = None,
        data: dict[str, str] | list[tuple] | str | BytesIO | bytes | None = None,
        json: dict | list | None = None,
        files: dict | None = None,
        auth: tuple[str, str] | None = None,
        timeout: float | tuple[float, float] | object | None = None,
        allow_redirects: bool | CurlFollow | str | None = None,
        max_redirects: int | None = None,
        proxies: ProxySpec | None = None,
        proxy: str | None = None,
        proxy_auth: tuple[str, str] | None = None,
        verify: bool | None = None,
        referer: str | None = None,
        accept_encoding: str | None = "gzip, deflate, br",
        content_callback: Callable[[bytes], None] | None = None,
        impersonate: BrowserTypeLiteral | None = None,
        ja3: str | None = None,
        akamai: str | None = None,
        perk: str | None = None,
        extra_fp: ExtraFingerprints | ExtraFpDict | None = None,
        default_headers: bool | None = None,
        default_encoding: str | Callable[[bytes], str] = "utf-8",
        quote: str | Literal[False] = "",
        http_version: CurlHttpVersion | HttpVersionLiteral | None = None,
        interface: str | None = None,
        cert: str | tuple[str, str] | None = None,
        stream: bool | None = None,
        max_recv_speed: int = 0,
        multipart: CurlMime | None = None,
        discard_cookies: bool = False,
    ) -> None:
        if body is not sentinel:
            warnings.warn(
                "parameter 'body' is deprecated, use 'json' or 'data' argument instead",
                category=AyugeSpiderToolsDeprecationWarning,
                stacklevel=2,
            )

        if isinstance(url, URL):
            url = str(url)

        curl_cffi_req_args = {
            "method": method,
            "url": url,
            "params": params,
            "data": data,
            "json": json,
            "headers": headers,
            "cookies": cookies,
            "files": files,
            "auth": auth,
            "timeout": timeout,
            "allow_redirects": allow_redirects,
            "max_redirects": max_redirects,
            "proxies": proxies,
            "proxy": proxy,
            "proxy_auth": proxy_auth,
            "verify": verify,
            "referer": referer,
            "accept_encoding": accept_encoding,
            "content_callback": content_callback,
            "impersonate": impersonate,
            "ja3": ja3,
            "akamai": akamai,
            "perk": perk,
            "extra_fp": extra_fp,
            "default_headers": default_headers,
            "default_encoding": default_encoding,
            "quote": quote,
            "http_version": http_version,
            "interface": interface,
            "cert": cert,
            "stream": stream,
            "max_recv_speed": max_recv_speed,
            "multipart": multipart,
            "discard_cookies": discard_cookies,
        }

        meta = copy.deepcopy(meta) or {}
        curl_cffi_meta = meta.setdefault("curl_cffi", {})
        curl_cffi_meta["args"] = curl_cffi_req_args

        super().__init__(
            url=url,
            callback=callback,
            method=method,
            headers=cast("ScrapyHeaders", headers),
            cookies=cast("ScrapyCookies", cookies),
            meta=meta,
            encoding=encoding,
            priority=priority,
            dont_filter=dont_filter,
            errback=errback,
            flags=flags,
            cb_kwargs=cb_kwargs,
        )

    def copy(self) -> CurlCffiRequest:
        curl_cffi_args = copy.deepcopy(self.meta.get("curl_cffi", {}).get("args", {}))
        meta = copy.deepcopy(self.meta)
        meta.pop("curl_cffi", None)

        return self.__class__(
            callback=self.callback,
            meta=meta,
            encoding=self.encoding,
            priority=self.priority,
            dont_filter=self.dont_filter,
            errback=self.errback,
            flags=self.flags,
            cb_kwargs=self.cb_kwargs,
            **curl_cffi_args,
        )
