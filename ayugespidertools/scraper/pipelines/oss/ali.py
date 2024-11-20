from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

import scrapy
from scrapy.http.request import NO_CALLBACK
from scrapy.utils.defer import maybe_deferred_to_future
from scrapy.utils.python import to_bytes

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.utils import Tools
from ayugespidertools.extras.oss import AliOssBase
from ayugespidertools.items import DataItem

__all__ = [
    "AyuAsyncOssPipeline",
    "files_download_by_scrapy",
]

if TYPE_CHECKING:
    from scrapy.http.response import Response

    from ayugespidertools.common.typevars import AlterItem, OssConf
    from ayugespidertools.spiders import AyuSpider


async def files_download_by_scrapy(spider: AyuSpider, url: str) -> tuple[Response, str]:
    request = scrapy.Request(url, callback=NO_CALLBACK)
    response = await maybe_deferred_to_future(spider.crawler.engine.download(request))
    headers_dict = Tools.get_dict_form_scrapy_req_headers(
        scrapy_headers=response.headers
    )
    content_type = headers_dict.get("Content-Type")
    file_format = content_type.split("/")[-1].replace("jpeg", "jpg")
    file_guid = hashlib.sha1(to_bytes(url)).hexdigest()
    filename = f"{file_guid}.{file_format}"
    return response, filename


class AyuAsyncOssPipeline:
    oss_bucket: AliOssBase
    oss_conf: OssConf
    full_link_enable: bool

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "oss_conf"), "未配置 oss 参数！"
        self.oss_conf = spider.oss_conf
        oss_conf_dict = self.oss_conf._asdict()
        self.oss_bucket = AliOssBase(**oss_conf_dict)
        self.full_link_enable = self.oss_conf.full_link_enable

    async def _upload_process(self, url: str, spider: AyuSpider) -> str:
        r, filename = await files_download_by_scrapy(spider, url)
        self.oss_bucket.put_oss(put_bytes=r.body, file=filename)
        if self.full_link_enable:
            filename = self.oss_bucket.get_full_link(filename)
        return filename

    def _add_oss_field(
        self, is_namedtuple: bool, item: Any, key: str, filename: str | list
    ) -> None:
        if not is_namedtuple:
            item[f"{self.oss_conf.oss_fields_prefix}{key}"] = filename
        else:
            item[f"{self.oss_conf.oss_fields_prefix}{key}"] = DataItem(
                key_value=filename, notes=f"{key} 对应的 oss 存储字段"
            )

    async def _upload_file(
        self, alter_item: AlterItem, item: Any, spider: AyuSpider
    ) -> None:
        if not (new_item := alter_item.new_item):
            return

        file_url_keys = {
            key: url
            for key, url in new_item.items()
            if key.endswith(self.oss_conf.upload_fields_suffix)
        }
        _is_namedtuple = alter_item.is_namedtuple
        for key, url in file_url_keys.items():
            if all([isinstance(url, str), url]):
                filename = await self._upload_process(url, spider)
                self._add_oss_field(_is_namedtuple, item, key, filename)

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alter_item = ReuseOperation.reshape_item(item_dict)
        await self._upload_file(alter_item, item, spider)
        return item
