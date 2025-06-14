from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.config import logger
from ayugespidertools.items import DataItem
from ayugespidertools.scraper.pipelines.oss.ali import files_download_by_scrapy

__all__ = ["FilesDownloadPipeline"]

if TYPE_CHECKING:
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.common.typevars import AlterItem
    from ayugespidertools.spiders import AyuSpider


class FilesDownloadPipeline:
    def __init__(self, file_path=None):
        self.file_path = file_path

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        _file_path = crawler.settings.get("FILES_STORE", None)
        assert _file_path is not None, "未配置 FILES_STORE 存储路径参数！"

        if not Path.exists(_file_path):
            logger.warning(f"FILES_STORE: {_file_path} 路径不存在，自动创建所需路径！")
            Path(_file_path).mkdir(parents=True)
        return cls(file_path=_file_path)

    async def _download_and_add_field(
        self, alter_item: AlterItem, item: Any, spider: AyuSpider
    ) -> None:
        if not (new_item := alter_item.new_item):
            return

        file_url_keys = {
            key: url for key, url in new_item.items() if key.endswith("_file_url")
        }
        _is_namedtuple = alter_item.is_namedtuple
        for key, url in file_url_keys.items():
            if all([isinstance(url, str), url]):
                r, filename = await files_download_by_scrapy(spider, url)
                Path(f"{self.file_path}/{filename}").write_bytes(r.body)
                # Store file in item
                if not _is_namedtuple:
                    item[f"{key}_local"] = filename
                else:
                    item[f"{key}_local"] = DataItem(
                        key_value=filename, notes=f"{key} 文件存储路径"
                    )

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alter_item = ReuseOperation.reshape_item(item_dict)
        await self._download_and_add_field(alter_item, item, spider)
        return item
