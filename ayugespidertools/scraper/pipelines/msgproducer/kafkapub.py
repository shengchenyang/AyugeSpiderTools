from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from kafka.errors import KafkaError

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.config import logger
from ayugespidertools.exceptions import NotConfigured
from ayugespidertools.utils.database import KafkaPortal

__all__ = ["AyuKafkaPipeline"]

if TYPE_CHECKING:
    from typing import Self

    from scrapy.crawler import Crawler

    from ayugespidertools.common.typevars import KafkaConf
    from ayugespidertools.spiders import AyuSpider


class KafkaProducerClient:
    def __init__(self, kafka_conf: KafkaConf) -> None:
        self.producer = KafkaPortal(db_conf=kafka_conf).connect()

    def sendmsg(self, topic: str, value: dict, key: str | None = None) -> None:
        """Send a message to Kafka and wait up to ten seconds for acknowledgement.

        Args:
            topic: Destination Kafka topic.
            value: message value. Must be type bytes, or be serializable to
                bytes via configured value_serializer. If value is None, key is
                required and message acts as a 'delete'.
            key: Optional message key passed to the configured key serializer.
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
            # Partition and offset metadata are not currently logged.
            # Successful result returns assigned partition and offset
            # partition = record_metadata.partition
            # offset = record_metadata.offset
            # logger.info(f"Kafka message delivered, partition: {partition}, offset: {offset}")
        except KafkaError:
            # Log the message context when delivery fails.
            logger.error(
                f"Failed to deliver Kafka message, topic: {topic}, value: {value}, key: {key}"
            )

    def on_send_success(self, *args, **kwargs):
        """Handle a successful send without additional logging."""
        return

    def on_send_error(self, excp: BaseException) -> None:
        """Log a Kafka message delivery failure."""
        logger.error(f"Kafka message delivery failed: {excp}")

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
        if not hasattr(spider, "kafka_conf"):
            raise NotConfigured(
                "[kafka] is not configured in either .conf or remote config."
            )
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
