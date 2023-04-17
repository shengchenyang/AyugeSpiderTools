import asyncio
import contextlib

import aiomysql

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = ["AsyncMysqlPipeline"]


class AsyncMysqlPipeline(AyuMysqlPipeline):
    def open_spider(self, spider):
        assert hasattr(spider, "mysql_conf"), "未配置 Mysql 连接信息！"

        self.slog = spider.slog
        self.mysql_conf = spider.mysql_conf
        self.collate = ToolsForAyu.get_collate_by_charset(mysql_conf=spider.mysql_conf)
        return ReuseOperation.as_deferred(self._open_spider(spider))

    async def _open_spider(self, spider):
        # aiomysql 所需要的配置
        self.pool = await aiomysql.create_pool(
            user=spider.mysql_conf.user,
            password=spider.mysql_conf.password,
            host=spider.mysql_conf.host,
            port=spider.mysql_conf.port,
            db=spider.mysql_conf.database,
            charset=spider.mysql_conf.charset,
        )
        # 创建列表以存储任务
        self.tasks = []

    def process_item(self, item, spider):
        # 创建任务以运行协程
        task = asyncio.create_task(self.insert_item(item, spider))
        # 将任务添加到列表
        self.tasks.append(task)
        return item

    async def insert_item(self, item, spider):
        async with self.pool.acquire() as aiomysql_conn:
            async with aiomysql_conn.cursor() as aiomysql_cursor:
                item_dict = ToolsForAyu.convert_items_to_dict(item)
                alter_item = super(AsyncMysqlPipeline, self).get_new_item(item_dict)
                table = super(AsyncMysqlPipeline, self).get_table_name(
                    item_dict["table"]
                )
                new_item = alter_item.new_item
                keys = f"""`{"`, `".join(new_item.keys())}`"""
                values = ", ".join(["%s"] * len(new_item))
                update = ",".join([f" `{key}` = %s" for key in new_item])
                sql = f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"

                await aiomysql_cursor.execute(sql, tuple(new_item.values()) * 2)
                await aiomysql_conn.commit()

    async def _close_spider(self):
        await self.pool.wait_closed()

    def close_spider(self, spider):
        self.pool.close()
        # 取消或等待所有任务完成
        for task in self.tasks:
            if not task.done():
                with contextlib.suppress(asyncio.CancelledError):
                    task.cancel()
            else:
                task.result()
        return ReuseOperation.as_deferred(self._close_spider())
