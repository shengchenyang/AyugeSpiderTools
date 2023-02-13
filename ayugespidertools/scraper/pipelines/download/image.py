import os
from urllib.parse import urlparse

from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline


class ImagesDownloadPipeline(ImagesPipeline):
    """
    图片下载场景的 scrapy pipeline 扩展
    """

    # TODO: 此方法暂用于测试
    def get_media_requests(self, item, info):
        if image_url := item.get("image_url"):
            return Request(image_url)
        print("No image_url")

    def item_completed(self, results, item, info):
        if image_paths := [x["path"] for ok, x in results if ok]:
            item["image_path"] = image_paths[0]
        return item

    def file_path(self, request, response=None, info=None, *, item=None):
        return f"images/{os.path.basename(urlparse(request.url).path)}"
