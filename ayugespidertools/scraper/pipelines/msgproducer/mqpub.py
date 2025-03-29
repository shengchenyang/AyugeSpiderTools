from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pika

from ayugespidertools.common.multiplexing import ReuseOperation

__all__ = [
    "AyuMQPipeline",
]

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

    from ayugespidertools.common.typevars import MQConf
    from ayugespidertools.spiders import AyuSpider


class AyuMQPipeline:
    channel: BlockingChannel
    conn: BlockingConnection

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "rabbitmq_conf"), "未配置 RabbitMQ 连接信息！"
        _mq_conf: MQConf = spider.rabbitmq_conf
        cluster_hosts = [h.strip() for h in _mq_conf.host.split(",")]
        parameters = [
            pika.ConnectionParameters(
                host=host,
                port=_mq_conf.port,
                virtual_host=_mq_conf.virtualhost,
                credentials=pika.PlainCredentials(
                    username=_mq_conf.username, password=_mq_conf.password
                ),
                heartbeat=_mq_conf.heartbeat,
                socket_timeout=_mq_conf.socket_timeout,
                connection_attempts=3,
                retry_delay=1,
            )
            for host in cluster_hosts
        ]

        self.conn = pika.BlockingConnection(parameters=parameters)
        self.channel = self.conn.channel()
        self.channel.queue_declare(
            queue=_mq_conf.queue,
            durable=_mq_conf.durable,
            exclusive=_mq_conf.exclusive,
            auto_delete=_mq_conf.auto_delete,
        )
        self.channel.confirm_delivery()

    def close_spider(self, spider: AyuSpider) -> None:
        self.conn.close()

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        publish_data = json.dumps(item_dict).encode()
        self.channel.basic_publish(
            exchange=spider.rabbitmq_conf.exchange,
            routing_key=spider.rabbitmq_conf.routing_key,
            body=publish_data,
            properties=pika.BasicProperties(
                content_type=spider.rabbitmq_conf.content_type,
                delivery_mode=spider.rabbitmq_conf.delivery_mode,
            ),
            mandatory=True,
        )
        return item
