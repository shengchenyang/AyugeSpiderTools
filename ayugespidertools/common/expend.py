import datetime
from typing import TYPE_CHECKING

import pymysql
from retrying import retry

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.config import logger

__all__ = [
    "MysqlPipeEnhanceMixin",
]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import MysqlConf


class MysqlPipeEnhanceMixin:
    """扩展 pipelines 的功能"""

    @retry(
        stop_max_attempt_number=Param.retry_num,
        wait_random_min=Param.retry_time_min,
        wait_random_max=Param.retry_time_max,
    )
    def _connect(
        self,
        mysql_conf: "MysqlConf",
    ) -> pymysql.connections.Connection:
        """链接数据库操作：
            1.如果链接正常，则返回链接句柄；
            2.如果目标数据库不存在，则创建数据库后再返回链接句柄。

        Args:
            mysql_conf: pymysql 链接所需的参数

        Returns:
            1). pymysql.connections.Connection, 链接句柄
        """
        try:
            conn = pymysql.connect(
                user=mysql_conf.user,
                password=mysql_conf.password,
                host=mysql_conf.host,
                port=mysql_conf.port,
                database=mysql_conf.database,
                charset=mysql_conf.charset,
            )
        except Exception as e:
            logger.warning(f"目标数据库：{mysql_conf.database} 不存在，尝试创建中...")
            if "1049" in str(e):
                # 如果连接目标数据库报不存在的错误时，先创建出此目标数据库
                ReuseOperation.create_database(mysql_conf)
        else:
            # 连接没有问题就直接返回连接对象
            return conn
        # 出现数据库不存在问题后，在创建数据库后，再次返回连接对象
        return pymysql.connect(
            user=mysql_conf.user,
            password=mysql_conf.password,
            host=mysql_conf.host,
            port=mysql_conf.port,
            database=mysql_conf.database,
            charset=mysql_conf.charset,
        )

    def _get_sql_by_item(self, table: str, item: dict) -> str:
        """根据处理后的 item 生成 sql 插入语句

        Args:
            table: 数据库表名
            item: 处理后的 item

        Returns:
            1). sql 插入语句
        """
        keys = f"""`{"`, `".join(item.keys())}`"""
        values = ", ".join(["%s"] * len(item))
        update = ",".join([f" `{key}` = %s" for key in item])
        return f"INSERT INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"

    def _get_log_by_spider(self, spider, crawl_time):
        """获取 spider 的运行日志情况

        Args:
            spider: scrapy spider
            crawl_time: 爬取时间

        Returns:
            log_info: 日志信息
        """
        mysql_conf = spider.mysql_conf
        text = {}
        stats = spider.crawler.stats.get_stats()
        error_reason = ""
        _curr_utc_time = datetime.datetime.now(datetime.timezone.utc)
        for k, v in stats.items():
            if isinstance(v, datetime.datetime):
                text[k.replace("/", "_")] = (v + datetime.timedelta(hours=8)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            else:
                if all(
                    [
                        "response_status_count" in k,
                        k != "downloader/response_status_count/200",
                    ]
                ):
                    status_code = k.split("/")[-1] if len(k.split("/")) > 0 else ""
                    if status_code.startswith("4"):
                        if status_code == "429":
                            error_reason += f"{status_code}错误：代理超过使用频率限制"
                        else:
                            error_reason += f"{status_code}错误：网页失效/无此网页/网站拒绝访问"
                    elif status_code.startswith("5"):
                        error_reason += f"{status_code}错误：网站服务器处理出错"
                    elif status_code != "":
                        error_reason += f"{status_code}:待人工排查原因"
                elif "exception_type_count" in k:
                    error_name = k.split("/")[-1]
                    if "Timeout" in error_name:
                        error_reason += f"{error_name}:网站响应超时错误 "
                    elif "ConnectionDone" in error_name:
                        error_reason += f"{error_name}:网站与脚本连接断开 "
                    else:
                        # "ResponseNeverReceived" or "ResponseFailed"
                        error_reason += f"{error_name}:网站无响应 "
                text[k.replace("/", "_")] = v

        log_info = {
            "database": mysql_conf.database,
            "spider_name": spider.name,
            "uid": f"{mysql_conf.database}|{spider.name}",
            "request_counts": text.get("downloader_request_count", 0),
            "received_count": text.get("response_received_count", 0),
            "item_counts": text.get("item_scraped_count", 0),
            "info_count": text.get("log_count_INFO", 0),
            "warning_count": text.get("log_count_WARNING", 0),
            "error_count": text.get("log_count_ERROR", 0),
            "start_time": text.get("start_time"),
            "finish_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "spend_minutes": round(
                (_curr_utc_time - stats.get("start_time")).seconds / 60,
                2,
            ),
            "crawl_time": crawl_time,
        }

        # 错误原因
        if text.get("log_count_ERROR", 0):
            log_info["log_count_ERROR"] = error_reason or "请人工排查错误原因！"

        else:
            log_info["log_count_ERROR"] = ""
        return log_info
