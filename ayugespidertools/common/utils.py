from __future__ import annotations

import json
import random
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlparse

from ayugespidertools.common.encryption import Encrypt
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.config import logger
from ayugespidertools.extras.ext import AppConfManageMixin

__all__ = ["Tools"]

if TYPE_CHECKING:
    from collections.abc import Iterable

    from scrapy.http import Response

    from ayugespidertools.common.typevars import Str_Lstr

RemoteFormatStr = Literal["json", "hcl", "yaml", "xml"]
RemoteTypeStr = Literal["consul", "nacos"]
RemoteConfNameStr = Literal[
    "mongodb",
    "mongodb:uri",
    "mysql",
    "postgresql",
    "elasticsearch",
    "oracle",
    "oss:ali",
    "rabbitmq",
    "kafka",
    "proxy",
]


class Tools(AppConfManageMixin):
    @staticmethod
    @lru_cache(maxsize=16)
    def get_remote_kvs(
        url: str, remote_type: RemoteTypeStr = "consul", token: str | None = None
    ) -> str:
        """Fetch a configuration value from Consul or Nacos.

        Args:
            url: URL of the remote configuration endpoint.
            remote_type: Configuration provider, either "consul" or "nacos".
            token: Consul ACL token. For Nacos, include the token in the URL.

        Returns:
            The configuration text, with Consul Base64 values decoded as needed.
        """
        headers = (
            {"X-Consul-Token": token}
            if all([remote_type == "consul", token is not None])
            else {}
        )
        req = urllib.request.Request(url=url, headers=headers)  # noqa: S310
        r = urllib.request.urlopen(req)  # noqa: S310
        data = r.read().decode(errors="ignore")

        url_params = urlparse(url).query
        if remote_type == "consul":
            if "raw" in url_params:
                return data

            json_data = json.loads(data)
            return Encrypt.base64_decode(decode_data=json_data[0]["Value"])
        return data

    @classmethod
    def fetch_remote_conf(
        cls,
        conf_name: RemoteConfNameStr,
        url: str,
        format: RemoteFormatStr = "json",
        remote_type: RemoteTypeStr = "consul",
        token: str | None = None,
    ) -> dict:
        conf_value = cls.get_remote_kvs(url, remote_type, token)
        if format == "json":
            conf_data = json.loads(conf_value)
        elif format == "xml":
            conf_data = cls.xml_parser(conf_value)
        elif format == "yaml":
            conf_data = cls.yaml_parser(conf_value)
        elif format == "hcl":
            conf_data = cls.hcl_parser(conf_value)
        else:
            raise ValueError(f"Unsupported configuration format for {conf_name}")

        _conf = conf_data.get(conf_name, {})
        if not _conf:
            logger.info(
                f"Configuration section {conf_name} is not set in {remote_type}"
            )
        return _conf

    @staticmethod
    def extract_with_css(
        response: Response,
        query: str,
        get_all: bool = False,
        return_selector: bool = False,
    ):
        if return_selector:
            return response.css(query)
        if get_all:
            return response.css(query).getall()
        return response.css(query).get(default="").strip()

    @staticmethod
    def extract_with_xpath(
        response: Response,
        query: str,
        get_all: bool = False,
        return_selector: bool = False,
    ):
        if return_selector:
            return response.xpath(query)
        if get_all:
            return response.xpath(query).getall()
        return response.xpath(query).get(default="").strip()

    @staticmethod
    def extract_with_json(
        json_data: dict, query: str | list[str], ignore_err: bool = False
    ) -> Any:
        # Handle a single key or a path containing only one key.
        if any(
            [isinstance(query, str), all([isinstance(query, list), len(query) == 1])]
        ):
            if isinstance(query, str):
                return json_data.get(query)
            return json_data.get(query[0], None)

        # Traverse the nested key path.
        for curr_q in query:
            if not isinstance(json_data, dict):
                if not ignore_err:
                    logger.error(
                        f"JSON extraction failed: expected a dictionary while traversing query {query}"
                    )
                return None

            json_data = json_data.get(curr_q)  # type: ignore[assignment]
            if json_data is None:
                return None
        return json_data

    @classmethod
    def extract_with_json_rules(
        cls, json_data: dict, query_rules: list[Str_Lstr], ignore_err: bool = False
    ):
        depth_num = ReuseOperation.get_array_depth(query_rules)
        assert depth_num <= 2, "query_rules must have a maximum nesting depth of 2"

        for query in query_rules:
            extract_res = cls.extract_with_json(
                json_data=json_data, query=query, ignore_err=ignore_err
            )
            if extract_res is not None:
                return extract_res
        return None

    @staticmethod
    def first_not_none(data_lst: Iterable[Any]) -> Any:
        """Get the first non-None value in an iterable.

        Args:
            data_lst: Iterable data.

        Returns:
            The first non-None value, or None if no such value exists.
        """
        _res = [x for x in data_lst if x is not None]
        return _res[0] if _res else None

    @staticmethod
    def get_data_urls_by_img(mediatype: str, data: bytes | str) -> str:
        """Generate a Data URL from a local file, remote resource, or bytes.

        Data URL examples:
            data:image/png;base64,iVB...
            data:text/html,%3Ch1%3EHello%2C%20World%21%3C%2Fh1%3E

        For more information about Data URLs, see:
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs

        Args:
            mediatype: The MIME type, such as 'image/jpeg' for JPEG images.
                If omitted, it defaults to 'text/plain;charset=US-ASCII'.
            data: The binary data to encode using Base64.
                Can be a local file path or raw bytes.

        Returns:
            The generated Data URL.
        """
        assert type(data) in [
            str,
            bytes,
        ], "data must be a local image file path (str) or raw image bytes"

        if isinstance(data, str):
            data_bytes = Path(data).read_bytes()
            data_base64_encoded = Encrypt.base64_encode(encode_data=data_bytes)

        else:
            data_base64_encoded = Encrypt.base64_encode(encode_data=data)
        return f"data:image/{mediatype};base64,{data_base64_encoded}"

    @staticmethod
    def gen_selenium_track(distance):
        distance += 20
        v = 0
        t = 0.2
        forward_tracks = []
        current = 0
        mid = distance * 3 / 5
        while current < distance:
            a = 2 if current < mid else -3
            s = v * t + 0.5 * a * (t**2)
            v = v + a * t
            current += s
            forward_tracks.append(round(s))

        back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
        return {"forward_tracks": forward_tracks, "back_tracks": back_tracks}

    @staticmethod
    def gen_tracks(distance):
        t_list = [random.randint(50, 160)]  # noqa: S311
        x_list = [random.randint(5, 11)]  # noqa: S311
        y_list = []
        for j in range(1, distance):
            x_list.append(x_list[j - 1] + random.randint(2, 4))  # noqa: S311
            if x_list[j] > distance:
                break

        diff = x_list[-1] - distance
        for _ in range(diff):
            x_list.append(x_list[-1] + random.randint(-2, -1))  # noqa: S311
            if x_list[-1] <= distance:
                x_list[-1] = distance
                break

        length = len(x_list)
        for i in range(1, length + 1):
            if i < int(length * 0.4):
                y_list.append(0)
            elif i < int(length * 0.65):
                y_list.append(-1)
            elif i < int(length * 0.77):
                y_list.append(-2)
            elif i < int(length * 0.95):
                y_list.append(-3)
            else:
                y_list.append(-4)
            t_list.append(t_list[i - 1] + random.randint(20, 80))  # noqa: S311

        xyt = list(zip(x_list, y_list, t_list, strict=False))
        for j in range(length):
            xyt[j] = list(xyt[j])
        return xyt
