from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

import pika

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.utils.database import RabbitMQPortal

__all__ = [
    "AyuMQPipeline",
]

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.common.typevars import MQConf
    from ayugespidertools.spiders import AyuSpider


class AyuMQPipeline:
    channel: BlockingChannel
    conn: BlockingConnection
    crawler: Crawler
    _declared_queues: set[str]

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "rabbitmq_conf"), "未配置 RabbitMQ 连接信息！"
        _mq_conf: MQConf = spider.rabbitmq_conf
        self.conn = RabbitMQPortal(db_conf=_mq_conf).connect()
        self.channel = self.conn.channel()
        self.channel.confirm_delivery()
        self._declared_queues = set()

    def _ensure_queue(self, queue_name: str) -> None:
        if queue_name in self._declared_queues:
            return

        spider = cast("AyuSpider", self.crawler.spider)
        _mq_conf: MQConf = spider.rabbitmq_conf
        self.channel.queue_declare(
            queue=queue_name,
            durable=_mq_conf.durable,
            exclusive=_mq_conf.exclusive,
            auto_delete=_mq_conf.auto_delete,
        )
        self._declared_queues.add(queue_name)

    def close_spider(self) -> None:
        self._declared_queues.clear()
        self.conn.close()

    def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alert_item = ReuseOperation.reshape_item(item_dict)
        if not (new_item := alert_item.new_item):
            return item

        spider = cast("AyuSpider", self.crawler.spider)
        table_name = alert_item.table.name
        queue_name = table_name or spider.rabbitmq_conf.queue
        routing_key = spider.rabbitmq_conf.get_routing_key(item_routing_key=table_name)
        self._ensure_queue(queue_name)
        publish_data = json.dumps(new_item).encode()
        self.channel.basic_publish(
            exchange=spider.rabbitmq_conf.exchange,
            routing_key=routing_key,
            body=publish_data,
            properties=pika.BasicProperties(
                content_type=spider.rabbitmq_conf.content_type,
                delivery_mode=spider.rabbitmq_conf.delivery_mode,
            ),
            mandatory=True,
        )
        return item
