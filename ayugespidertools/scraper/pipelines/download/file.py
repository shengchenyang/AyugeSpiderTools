import hashlib
from pathlib import Path
from typing import Literal

import scrapy
from scrapy.http.request import NO_CALLBACK
from scrapy.utils.defer import maybe_deferred_to_future

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.config import logger
from ayugespidertools.items import DataItem

__all__ = [
    "FilesDownloadPipeline",
]

DataItemModeStr = Literal["normal", "namedtuple", "dict"]


class FilesDownloadPipeline:
    """文件下载的 scrapy pipeline 扩展"""

    _type: DataItemModeStr = "normal"

    def __init__(self, file_path=None):
        self.file_path = file_path

    @classmethod
    def from_crawler(cls, crawler):
        _file_path = crawler.settings.get("FILES_STORE", None)
        assert _file_path is not None, "未配置 FILES_STORE 存储路径参数！"

        if not Path.exists(_file_path):
            logger.warning(f"FILES_STORE: {_file_path} 路径不存在，自动创建所需路径！")
            Path(_file_path).mkdir(parents=True)
        return cls(file_path=_file_path)

    async def process_item(self, item, spider):
        item_dict = ReuseOperation.item_to_dict(item)
        judge_item = next(iter(item_dict.values()))
        if ReuseOperation.is_namedtuple_instance(judge_item):
            self._type = "namedtuple"
            file_url = item_dict.get("file_url").key_value
            file_format = item_dict.get("file_format").key_value
        else:
            file_url = item_dict.get("file_url")
            file_format = item_dict.get("file_format")

        assert (
            file_format is not None
        ), "使用文件下载 pipelines 时，其 item 中 file_format 字段可能未设置！"

        if any([not file_url, not file_format]):
            return item

        if file_url is not None:
            request = scrapy.Request(file_url, callback=NO_CALLBACK)
            response = await maybe_deferred_to_future(
                spider.crawler.engine.download(request)
            )

            if response.status != 200:
                # Error happened, return item.
                return item

            # Save screenshot to file, filename will be hash of url.
            url_hash = hashlib.md5(file_url.encode("utf8")).hexdigest()
            filename = f"{self.file_path}/{url_hash}.{file_format}"
            Path(filename).write_bytes(response.body)

            # Store filename in item.
            if self._type == "namedtuple":
                item["_filename"] = DataItem(key_value=filename, notes="文件存储路径")
            else:
                item["_filename"] = filename
        return item
