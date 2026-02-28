from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from typing_extensions import Self

from ayugespidertools.common.typevars import MQConf
from ayugespidertools.config import get_cfg
from ayugespidertools.exceptions import NotConfigured
from ayugespidertools.spiders import AyuSpider
from ayugespidertools.utils.database import RabbitMQAsyncPortal

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import aio_pika


__all__ = ["AyuRabbitMQSpider"]


class AyuRabbitMQSpider(AyuSpider):
    task_mq_conf: MQConf

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs) -> Self:
        spider = cast("Self", super().from_crawler(crawler, *args, **kwargs))
        spiders_conf: dict = crawler.settings.get("AYUSPIDERS_CONFIG", {})
        spider_conf = spiders_conf.get(spider.name)
        if not spider_conf:
            raise NotConfigured(f"No spider config found for spider '{spider.name}'")

        mq_queue = spider_conf.get("task_mq")
        if not mq_queue:
            raise NotConfigured(f"'task_mq' not configured for spider '{spider.name}'")

        _my_cfg = get_cfg()
        if not _my_cfg.has_section(mq_queue):
            raise NotConfigured(
                f"'{mq_queue}' not configured for spider '{spider.name}'"
            )
        task_mq_option = _my_cfg[mq_queue]
        spider.task_mq_conf = MQConf(
            host=task_mq_option.get("host"),
            port=task_mq_option.getint("port"),
            username=task_mq_option.get("username"),
            password=task_mq_option.get("password"),
            virtualhost=task_mq_option.get("virtualhost"),
        )
        spider.crawler = crawler
        return spider

    async def start(self):
        self.slog.info("Starting RabbitMQ consumer (async start)")
        spider = cast("AyuRabbitMQSpider", self.crawler.spider)
        connection = await RabbitMQAsyncPortal(db_conf=spider.task_mq_conf).connect()
        async with connection:
            queue_name = self.rabbitmq_conf.queue
            channel: aio_pika.abc.AbstractChannel = await connection.channel()
            queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
                queue_name,
                durable=True,
                auto_delete=False,
            )

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        task_info = json.loads(message.body.decode())
                        async for req in self.start_requests_from_mq(task_info):
                            yield req

    async def start_requests_from_mq(self, msg: dict) -> AsyncIterator[Any]:
        yield
        raise NotImplementedError(
            f"{self.__class__.__name__}.start_requests_from_mq callback is not defined. ",
            "AyuRabbitMQSpider must implement the 'start_requests_from_mq' method.",
        )
