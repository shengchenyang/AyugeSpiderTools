import asyncio
import contextlib

import aiomysql

from ayugespidertools.common.MultiPlexing import ReuseOperation
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.scraper.pipelines.mysql import AyuMysqlPipeline

__all__ = ["AsyncMysqlPipeline"]


class AsyncMysqlPipeline(AyuMysqlPipeline):
    def open_spider(self, spider):
        assert hasattr(spider, "mysql_config"), "未配置 Mysql 连接信息！"

        self.slog = spider.slog
        self.mysql_config = spider.mysql_config
        self.collate = ToolsForAyu.get_collate_by_charset(
            mysql_config=self.mysql_config
        )
        return ReuseOperation.as_deferred(self._open_spider(spider))

    async def _open_spider(self, spider):
        # 将 mysql_config 改为 aiomysql 所需要的配置
        self.mysql_config["db"] = self.mysql_config.pop("database")
        self.mysql_config["cursorclass"] = aiomysql.DictCursor
        self.pool = await aiomysql.create_pool(**self.mysql_config)
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
                item_o = super(AsyncMysqlPipeline, self).get_new_item(item_dict)
                table = super(AsyncMysqlPipeline, self).get_table_name(
                    item_dict["table"]
                )
                new_item = item_o.get("new_item")
                # note_dic = item_o.get("notes_dic")
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
