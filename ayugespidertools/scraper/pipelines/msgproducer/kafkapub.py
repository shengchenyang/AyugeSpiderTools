from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from kafka import KafkaProducer
from kafka.errors import KafkaError

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.config import logger

__all__ = ["AyuKafkaPipeline"]

if TYPE_CHECKING:
    from scrapy.crawler import Crawler
    from typing_extensions import Self

    from ayugespidertools.common.typevars import KafkaConf
    from ayugespidertools.spiders import AyuSpider


class KafkaProducerClient:
    def __init__(self, kafka_conf: KafkaConf) -> None:
        # 如果有多个 kafka 服务地址，用逗号分隔，会在此处拆分为列表
        _bts = kafka_conf.bootstrap_servers
        bts_lst = _bts.split(",")
        producer_kwargs = {
            "bootstrap_servers": bts_lst,
            "key_serializer": lambda k: json.dumps(k).encode(),
            "value_serializer": lambda v: json.dumps(v).encode(),
        }
        if kafka_conf.security_protocol:
            producer_kwargs |= {
                "security_protocol": kafka_conf.security_protocol,
                "sasl_mechanism": kafka_conf.sasl_mechanism,
                "sasl_plain_username": kafka_conf.user,
                "sasl_plain_password": kafka_conf.password,
            }
        self.producer = KafkaProducer(**producer_kwargs)

    def sendmsg(self, topic: str, value: dict, key: str | None = None) -> None:
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

    def close_producer(self):
        if self.producer:
            self.producer.close()


class AyuKafkaPipeline:
    kp: KafkaProducerClient
    crawler: Crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        s = cls()
        s.crawler = crawler
        return s

    def open_spider(self) -> None:
        spider = cast("AyuSpider", self.crawler.spider)
        assert hasattr(spider, "kafka_conf"), "未配置 kafka 连接信息！"
        self.kp = KafkaProducerClient(kafka_conf=spider.kafka_conf)

    def process_item(self, item: Any) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alert_item = ReuseOperation.reshape_item(item_dict)
        if not (new_item := alert_item.new_item):
            return item

        spider = cast("AyuSpider", self.crawler.spider)
        self.kp.sendmsg(
            topic=spider.kafka_conf.topic,
            value=new_item,
            key=spider.kafka_conf.key,
        )
        return item

    def close_spider(self) -> None:
        self.kp.close_producer()
