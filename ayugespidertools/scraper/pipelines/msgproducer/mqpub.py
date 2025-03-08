from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pika

from ayugespidertools.common.expend import RabbitMqEnhanceMixin

__all__ = [
    "AyuMQPipeline",
]

if TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

    from ayugespidertools.common.typevars import MQConf
    from ayugespidertools.spiders import AyuSpider


class AyuMQPipeline(RabbitMqEnhanceMixin):
    channel: BlockingChannel
    conn: BlockingConnection

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "rabbitmq_conf"), "未配置 RabbitMQ 连接信息！"
        _mq_conf: MQConf = spider.rabbitmq_conf
        mq_conn_param = pika.URLParameters(
            f"amqp://{_mq_conf.username}:{_mq_conf.password}"
            f"@{_mq_conf.host}:{_mq_conf.port}/{_mq_conf.virtualhost}"
            f"?heartbeat={_mq_conf.heartbeat}&socket_timeout={_mq_conf.socket_timeout}"
        )
        self.conn = pika.BlockingConnection(parameters=mq_conn_param)
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
        self.channel.basic_publish(
            exchange=spider.rabbitmq_conf.exchange,
            routing_key=spider.rabbitmq_conf.routing_key,
            body=self.item_to_bytes(item),
            properties=pika.BasicProperties(
                content_type=spider.rabbitmq_conf.content_type,
                delivery_mode=spider.rabbitmq_conf.delivery_mode,
            ),
            mandatory=True,
        )
        return item
