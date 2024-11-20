from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ayugespidertools.extras.oss import AliOssBase
from ayugespidertools.scraper.pipelines.oss.ali import AyuAsyncOssPipeline

__all__ = [
    "AyuAsyncOssBatchPipeline",
]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import AlterItem, OssConf
    from ayugespidertools.spiders import AyuSpider


class AyuAsyncOssBatchPipeline(AyuAsyncOssPipeline):
    """适用于 oss 上传时，对应的文件资源字段为列表类型的场景"""

    oss_bucket: AliOssBase
    oss_conf: OssConf
    full_link_enable: bool

    async def _upload_file(self, alter_item: AlterItem, item: Any, spider: AyuSpider):
        if not (new_item := alter_item.new_item):
            return

        file_url_keys = {
            key: value
            for key, value in new_item.items()
            if key.endswith(self.oss_conf.upload_fields_suffix)
        }
        _is_namedtuple = alter_item.is_namedtuple
        for key, value in file_url_keys.items():
            if all([isinstance(value, str), value]):
                filename = await self._upload_process(value, spider)
                self._add_oss_field(_is_namedtuple, item, key, filename)

            elif isinstance(value, list):
                filename_lst = []
                for curr_val in value:
                    if all([isinstance(curr_val, str), curr_val]):
                        filename = await self._upload_process(curr_val, spider)
                        filename_lst.append(filename)
                if filename_lst:
                    self._add_oss_field(_is_namedtuple, item, key, filename_lst)
