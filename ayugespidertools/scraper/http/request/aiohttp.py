import copy
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    AnyStr,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)

from scrapy import Request

__all__ = [
    "AiohttpRequest",
]

if TYPE_CHECKING:
    from ssl import SSLContext

    from aiohttp.client import ClientTimeout
    from aiohttp.client_reqrep import ClientResponse, Fingerprint
    from aiohttp.helpers import BasicAuth
    from aiohttp.typedefs import LooseHeaders


class AiohttpRequest(Request):
    """为 scrapy 的 Request 对象添加额外的参数"""

    def __init__(
        self,
        url: str,
        callback: Optional[Callable] = None,
        method: str = "GET",
        headers: Union[Mapping[AnyStr, Any], Iterable[Tuple[AnyStr, Any]], None] = None,
        cookies: Optional[Union[dict, List[dict]]] = None,
        meta: Optional[Dict[str, Any]] = None,
        encoding: str = "utf-8",
        priority: int = 0,
        dont_filter: bool = False,
        errback: Optional[Callable] = None,
        flags: Optional[List[str]] = None,
        cb_kwargs: Optional[dict] = None,
        params: Optional[Mapping[str, str]] = None,
        data: Any = None,
        json: Any = None,
        skip_auto_headers: Optional[Iterable[str]] = None,
        auth: Optional["BasicAuth"] = None,
        allow_redirects: Optional[bool] = None,
        max_redirects: Optional[int] = None,
        compress: Optional[str] = None,
        chunked: Optional[bool] = None,
        expect100: Optional[bool] = None,
        raise_for_status: Union[
            None, bool, Callable[["ClientResponse"], Awaitable[None]]
        ] = None,
        read_until_eof: Optional[bool] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional["BasicAuth"] = None,
        verify_ssl: Optional[bool] = None,
        fingerprint: Optional[bytes] = None,
        ssl_context: Optional["SSLContext"] = None,
        ssl: Union["SSLContext", bool, "Fingerprint"] = True,
        server_hostname: Optional[str] = None,
        proxy_headers: Optional["LooseHeaders"] = None,
        trace_request_ctx: Optional[SimpleNamespace] = None,
        read_bufsize: Optional[int] = None,
        auto_decompress: Optional[bool] = None,
        max_line_size: Optional[int] = None,
        max_field_size: Optional[int] = None,
        timeout: Optional["ClientTimeout"] = None,
    ) -> None:

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
        }

        meta = copy.deepcopy(meta) or {}
        aiohttp_meta = meta.setdefault("aiohttp", {})
        aiohttp_meta["args"] = aiohttp_req_args

        super(AiohttpRequest, self).__init__(
            url=url,
            callback=callback,
            method=method,
            headers=headers,
            cookies=cookies,
            meta=meta,
            encoding=encoding,
            priority=priority,
            dont_filter=dont_filter,
            errback=errback,
            flags=flags,
            cb_kwargs=cb_kwargs,
        )
