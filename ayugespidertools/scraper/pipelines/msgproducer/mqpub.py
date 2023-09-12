import json

import pika

__all__ = [
    "AyuMQPipeline",
]


class AyuMQPipeline:
    """消息队列发布场景的 scrapy pipeline 扩展 - pika mq"""

    def __init__(self):
        self.channel = None

    def _dict_to_bytes(self, item: dict) -> bytes:
        item_json_str = json.dumps(item)
        return bytes(item_json_str, encoding="utf-8")

    def open_spider(self, spider):
        assert hasattr(
            spider, "rabbitmq_conf"
        ), "未配置 RabbitMQ 连接信息，请查看 .conf 或 consul 上对应配置信息！"

        _mq_conf = spider.rabbitmq_conf
        mq_conn_param = pika.URLParameters(
            f"amqp://{_mq_conf.username}:{_mq_conf.password}"
            f"@{_mq_conf.host}:{_mq_conf.port}/{_mq_conf.virtualhost}"
            f"?heartbeat={_mq_conf.heartbeat}&socket_timeout={_mq_conf.socket_timeout}"
        )
        conn = pika.BlockingConnection(parameters=mq_conn_param)
        self.channel = conn.channel()
        self.channel.queue_declare(
            queue=_mq_conf.queue,
            durable=_mq_conf.durable,
            exclusive=_mq_conf.exclusive,
            auto_delete=_mq_conf.auto_delete,
        )
        self.channel.confirm_delivery()

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.channel.basic_publish(
            exchange=spider.rabbitmq_conf.exchange,
            routing_key=spider.rabbitmq_conf.routing_key,
            body=self._dict_to_bytes(item),
            properties=pika.BasicProperties(
                content_type=spider.rabbitmq_conf.content_type,
                delivery_mode=spider.rabbitmq_conf.delivery_mode,
            ),
            mandatory=True,
        )
        return item
