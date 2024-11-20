from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from kafka import KafkaProducer
from kafka.errors import KafkaError

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.config import logger

__all__ = ["AyuKafkaPipeline"]

if TYPE_CHECKING:
    from ayugespidertools.spiders import AyuSpider


class KafkaProducerClient:
    def __init__(self, bootstrap_servers: list) -> None:
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda k: json.dumps(k).encode(),
            value_serializer=lambda v: json.dumps(v).encode(),
        )

    def sendmsg(
        self,
        topic: str,
        value: dict,
        key: str | None = None,
    ) -> None:
        """发送数据

        Args:
            topic: kafka topic
            value: message value. Must be type bytes, or be serializable to
                bytes via configured value_serializer. If value is None, key is
                required and message acts as a 'delete'.
            key: kafka key
        """
        # Asynchronous by default
        future = (
            self.producer.send(
                topic=topic,
                value=value,
                key=key,
            )
            .add_callback(self.on_send_success)
            .add_errback(self.on_send_error)
        )

        # Block for 'synchronous' sends
        try:
            _ = future.get(timeout=10)
            # 暂不需要日志记录成功后 _ 的 partition 和 offset，故注释掉
            # Successful result returns assigned partition and offset
            # partition = record_metadata.partition
            # offset = record_metadata.offset
            # logger.info(f"save success, partition: {partition}, offset: {offset}")
        except KafkaError:
            # Decide what to do if produce request failed...
            logger.error(f"save error, topic: {topic}, value: {value}, key: {key}")

    def on_send_success(self, *args, **kwargs):
        """发送成功回调函数，暂不做任何处理或提示"""
        return

    def on_send_error(self, data, key):
        """发送失败回调函数，只日志记录"""
        logger.error(f"send error, data: {data}, key: {key}")
        return

    def close_producer(self):
        if self.producer:
            self.producer.close()


class AyuKafkaPipeline:
    kp: KafkaProducerClient

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "kafka_conf"), "未配置 kafka 连接信息！"
        # 如果有多个 kafka 服务地址，用逗号分隔，会在此处拆分为列表
        _bts = spider.kafka_conf.bootstrap_servers
        bts_lst = _bts.split(",")
        self.kp = KafkaProducerClient(bootstrap_servers=bts_lst)

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        self.kp.sendmsg(
            topic=spider.kafka_conf.topic,
            value=item_dict,
            key=spider.kafka_conf.key,
        )
        return item

    def close_spider(self, spider: AyuSpider) -> None:
        self.kp.close_producer()
