import json
from typing import Any, Dict

import pika
import pika.exceptions

from ayugespidertools.common.typevars import MQConf

__all__ = [
    "AyuMQPipeline",
]


class AyuMQPipeline:
    """
    消息队列发布场景的 scrapy pipeline 扩展 - pika mq
    """

    def __init__(
        self,
        mq_conf: Dict[str, Any] = None,
    ) -> None:
        """
        初始化
        Args:
            mq_conf: mq 的连接配置
        """
        self.mq_conf = self._get_mq_args(conf=mq_conf)
        self.channel = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mq_conf=crawler.settings.get("MQ_CONFIG"),
        )

    def _get_mq_args(self, conf: Dict[str, Any]) -> MQConf:
        return MQConf(
            host=conf.get("host"),
            port=conf.get("port"),
            username=conf.get("username"),
            password=conf.get("password"),
            virtualhost=conf.get("virtualhost"),
            queue=conf.get("queue"),
            durable=conf.get("durable"),
            exclusive=conf.get("exclusive"),
            auto_delete=conf.get("auto_delete"),
            exchange=conf.get("exchange"),
            routing_key=conf.get("routing_key"),
            content_type=conf.get("content_type"),
            delivery_mode=conf.get("delivery_mode"),
            mandatory=conf.get("mandatory"),
        )

    def _dict_to_bytes(self, item: dict) -> bytes:
        item_json_str = json.dumps(item)
        return bytes(item_json_str, encoding="utf-8")

    def open_spider(self, spider):
        _mq_conn_param = pika.URLParameters(
            f"amqp://{self.mq_conf.username}:{self.mq_conf.password}@{self.mq_conf.host}"
            f":{self.mq_conf.port}/{self.mq_conf.virtualhost}?heartbeat=0&socket_timeout=1"
        )
        conn = pika.BlockingConnection(parameters=_mq_conn_param)
        self.channel = conn.channel()
        self.channel.queue_declare(
            queue=self.mq_conf.queue,
            durable=self.mq_conf.durable,
            exclusive=self.mq_conf.exclusive,
            auto_delete=self.mq_conf.auto_delete,
        )
        self.channel.confirm_delivery()

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.channel.basic_publish(
            exchange=self.mq_conf.exchange,
            routing_key=self.mq_conf.routing_key,
            body=self._dict_to_bytes(item),
            properties=pika.BasicProperties(
                content_type=self.mq_conf.content_type,
                delivery_mode=self.mq_conf.delivery_mode,
            ),
            mandatory=True,
        )
        return item
