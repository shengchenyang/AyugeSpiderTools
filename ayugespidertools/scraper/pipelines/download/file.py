import os
from urllib.parse import urlparse

from scrapy import Request
from scrapy.pipelines.files import FilesPipeline

__all__ = ["FilesDownloadPipeline"]


class FilesDownloadPipeline(FilesPipeline):
    """
    文件下载场景的 scrapy pipeline 扩展
    """

    # TODO: 此方法暂用于测试
    def get_media_requests(self, item, info):
        if file_url := item.get("file_url"):
            return Request(file_url)
        print("No file_url")

    def item_completed(self, results, item, info):
        if file_paths := [x["path"] for ok, x in results if ok]:
            item["file_path"] = file_paths[0]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return f"files/{os.path.basename(urlparse(request.url).path)}"
