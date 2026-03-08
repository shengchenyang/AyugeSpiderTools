from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

import aio_pika

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.utils.database import RabbitMQAsyncPortal

__all__ = [
    "AyuAsyncMQPipeline",
]

if TYPE_CHECKING:
    from aio_pika import RobustConnection
    from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractRobustConnection
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.common.typevars import MQConf
    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMQPipeline:
    mq_conf: MQConf
    connection: RobustConnection | AbstractRobustConnection
    channel: AbstractChannel
    exchange: AbstractExchange | None
    crawler: Crawler
    _declared_queues: set[str]

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    async def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "rabbitmq_conf"), "未配置 RabbitMQ 连接信息！"
        self.mq_conf = spider.rabbitmq_conf
        self._declared_queues: set[str] = set()
        self.exchange = None
        await self._open_spider()

    async def _open_spider(self) -> None:
        self.connection = await RabbitMQAsyncPortal(db_conf=self.mq_conf).connect()
        self.channel = await self.connection.channel()
        if exchange := self.mq_conf.exchange:
            self.exchange = await self.channel.declare_exchange(
                name=exchange,
                type=aio_pika.ExchangeType.DIRECT,
                durable=self.mq_conf.durable,
                auto_delete=self.mq_conf.auto_delete,
            )

    async def _declare_queue_if_needed(self, queue_name: str, routing_key: str) -> None:
        if queue_name in self._declared_queues:
            return

        queue = await self.channel.declare_queue(
            queue_name, durable=self.mq_conf.durable
        )
        if self.exchange:
            await queue.bind(self.exchange, routing_key=routing_key)
        self._declared_queues.add(queue_name)

    async def insert_item(self, publish_data: bytes, routing_key: str) -> None:
        if not self.exchange:
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=publish_data), routing_key=routing_key
            )
        else:
            await self.exchange.publish(
                aio_pika.Message(body=publish_data), routing_key=routing_key
            )

    async def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alert_item = ReuseOperation.reshape_item(item_dict)
        if not (new_item := alert_item.new_item):
            return item

        table_name = alert_item.table.name
        queue_name = table_name or self.mq_conf.queue
        routing_key = self.mq_conf.get_routing_key(item_routing_key=table_name)
        await self._declare_queue_if_needed(
            queue_name=queue_name, routing_key=routing_key
        )
        publish_data = json.dumps(new_item).encode()
        await self.insert_item(publish_data, routing_key)
        return item

    async def close_spider(self) -> None:
        self._declared_queues.clear()
        await self.connection.close()
