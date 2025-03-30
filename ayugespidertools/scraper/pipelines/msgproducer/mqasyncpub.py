from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import aio_pika
from scrapy.utils.defer import deferred_from_coro

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.exceptions import UnsupportedError

__all__ = [
    "AyuAsyncMQPipeline",
]

if TYPE_CHECKING:
    from aio_pika import RobustConnection
    from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractRobustConnection
    from twisted.internet.defer import Deferred

    from ayugespidertools.common.typevars import MQConf
    from ayugespidertools.spiders import AyuSpider


class AyuAsyncMQPipeline:
    mq_conf: MQConf
    connection: RobustConnection | AbstractRobustConnection
    channel: AbstractChannel
    exchange: AbstractExchange | None

    def open_spider(self, spider: AyuSpider) -> Deferred:
        assert hasattr(spider, "rabbitmq_conf"), "未配置 RabbitMQ 连接信息！"
        self.mq_conf = spider.rabbitmq_conf
        self.exchange = None
        return deferred_from_coro(self._open_spider(spider))

    async def _open_spider(self, spider: AyuSpider) -> None:
        if "," in self.mq_conf.host:
            raise UnsupportedError(
                "The host parameter in AyuAsyncMQPipeline cannot contain commas. "
                "Modify the host parameter in the [mq] section of the .conf file."
            )
        self.connection = await aio_pika.connect_robust(
            host=self.mq_conf.host,
            port=self.mq_conf.port,
            login=self.mq_conf.username,
            password=self.mq_conf.password,
            virtualhost=self.mq_conf.virtualhost,
        )
        self.channel = await self.connection.channel()
        if exchange := self.mq_conf.exchange:
            self.exchange = await self.channel.declare_exchange(
                name=exchange,
                type=aio_pika.ExchangeType.DIRECT,
                durable=self.mq_conf.durable,
                auto_delete=self.mq_conf.auto_delete,
            )
            queue = await self.channel.declare_queue(
                name=self.mq_conf.queue,
                durable=self.mq_conf.durable,
            )
            await queue.bind(exchange, routing_key=self.mq_conf.routing_key)

    async def insert_item(self, publish_data: bytes) -> None:
        if not self.exchange:
            await self.channel.default_exchange.publish(
                aio_pika.Message(body=publish_data),
                routing_key=self.mq_conf.routing_key,
            )
        else:
            await self.exchange.publish(
                aio_pika.Message(body=publish_data),
                routing_key=self.mq_conf.routing_key,
            )

    async def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        publish_data = json.dumps(item_dict).encode()
        await self.insert_item(publish_data)
        return item

    async def _close_spider(self) -> None:
        await self.connection.close()

    def close_spider(self, spider: AyuSpider) -> Deferred:
        return deferred_from_coro(self._close_spider())
