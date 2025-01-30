from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Union

from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.exceptions import NotConfigured
from ayugespidertools.scraper.pipelines.es import dynamic_es_document

try:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.helpers import async_bulk
except ImportError:
    raise NotConfigured(
        "missing elasticsearch library, please install it. "
        "install command: pip install ayugespidertools[database]"
    )

__all__ = ["AyuAsyncESPipeline"]

if TYPE_CHECKING:
    from elasticsearch_dsl import Document
    from twisted.internet.defer import Deferred

    from ayugespidertools.common.typevars import ESConf
    from ayugespidertools.spiders import AyuSpider

    DocumentType = Union[type[Document], type]


class AyuAsyncESPipeline:
    es_conf: ESConf
    client: AsyncElasticsearch
    es_type: DocumentType
    running_tasks: set

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "es_conf"), "未配置 elasticsearch 连接信息！"
        self.running_tasks = set()
        self.es_conf = spider.es_conf
        _hosts_lst = self.es_conf.hosts.split(",")
        if any([self.es_conf.user is not None, self.es_conf.password is not None]):
            http_auth = (self.es_conf.user, self.es_conf.password)
        else:
            http_auth = None
        self.client = AsyncElasticsearch(
            hosts=_hosts_lst,
            basic_auth=http_auth,
            verify_certs=self.es_conf.verify_certs,
            ca_certs=self.es_conf.ca_certs,
            client_cert=self.es_conf.client_cert,
            client_key=self.es_conf.client_key,
            ssl_assert_fingerprint=self.es_conf.ssl_assert_fingerprint,
        )

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alert_item = ReuseOperation.reshape_item(item_dict)
        if not (new_item := alert_item.new_item):
            return

        _index = alert_item.table.name
        if not hasattr(self, "es_type"):
            fields_define = {k: v.notes for k, v in item_dict.items()}
            index_define = self.es_conf.index_class
            index_define["name"] = _index
            self.es_type = dynamic_es_document("ESType", fields_define, index_define)
            if self.es_conf.init:
                self.es_type.init()

        task = asyncio.create_task(self.insert_item(new_item, _index))
        self.running_tasks.add(task)
        await task
        task.add_done_callback(lambda t: self.running_tasks.discard(t))
        return item

    async def insert_item(self, new_item: dict, index: str) -> None:
        async def gendata():
            yield {
                "_index": index,
                "doc": new_item,
            }

        await async_bulk(self.client, gendata())

    async def _close_spider(self):
        await self.client.close()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        return deferred_from_coro(self._close_spider())
