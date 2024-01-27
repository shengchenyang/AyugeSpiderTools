import hashlib
from typing import TYPE_CHECKING, Any

import scrapy
from scrapy.http.request import NO_CALLBACK
from scrapy.utils.defer import maybe_deferred_to_future
from scrapy.utils.python import to_bytes

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.extras.oss import AliOssBase
from ayugespidertools.items import DataItem

__all__ = ["AyuAsyncOssPipeline"]

if TYPE_CHECKING:
    from scrapy import Spider

    from ayugespidertools.common.typevars import OssConf


async def files_download_by_scrapy(
    spider: "Spider",
    file_url: str,
    item: Any,
):
    request = scrapy.Request(file_url, callback=NO_CALLBACK)
    response = await maybe_deferred_to_future(spider.crawler.engine.download(request))
    if response.status != 200:
        return item

    headers_dict = ToolsForAyu.get_dict_form_scrapy_req_headers(
        scrapy_headers=response.headers
    )
    content_type = headers_dict.get("Content-Type")
    file_format = content_type.split("/")[-1].replace("jpeg", "jpg")
    file_guid = hashlib.sha1(to_bytes(file_url)).hexdigest()
    filename = f"{file_guid}.{file_format}"
    return response, filename


class AyuAsyncOssPipeline:
    oss_bucket: AliOssBase
    oss_conf: "OssConf"

    def open_spider(self, spider):
        assert hasattr(spider, "oss_conf"), "未配置 oss 参数！"
        self.oss_conf = spider.oss_conf
        oss_conf_dict = self.oss_conf._asdict()
        self.oss_bucket = AliOssBase(**oss_conf_dict)

    async def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        judge_item = next(iter(item_dict.values()))
        file_url_keys = {
            key: value
            for key, value in item_dict.items()
            if key.endswith(self.oss_conf.upload_fields_suffix)
        }

        if ReuseOperation.is_namedtuple_instance(judge_item):
            for key, value in file_url_keys.items():
                file_url = value.key_value
                r, filename = await files_download_by_scrapy(spider, file_url, item)

                self.oss_bucket.put_oss(put_bytes=r.body, file=filename)
                item[f"{self.oss_conf.oss_fields_prefix}{key}"] = DataItem(
                    key_value=filename, notes=f"{key} 对应的 oss 存储字段"
                )

        else:
            for key, value in file_url_keys.items():
                r, filename = await files_download_by_scrapy(spider, value, item)

                self.oss_bucket.put_oss(put_bytes=r.body, file=filename)
                item[f"{self.oss_conf.oss_fields_prefix}{key}"] = filename

        return item
