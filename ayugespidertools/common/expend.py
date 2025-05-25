from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from retrying import retry

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param
from ayugespidertools.common.typevars import InsertPrefixStr, PortalTag
from ayugespidertools.config import logger
from ayugespidertools.utils.database import MysqlPortal, OraclePortal, PostgreSQLPortal

__all__ = [
    "MysqlPipeEnhanceMixin",
    "PostgreSQLPipeEnhanceMixin",
    "OraclePipeEnhanceMixin",
]

if TYPE_CHECKING:
    from oracledb.connection import Connection as OracleConnection
    from psycopg.connection import Connection as PsycopgConnection
    from pymysql.connections import Connection as PymysqlConnection

    from ayugespidertools.common.typevars import MysqlConf, OracleConf, PostgreSQLConf


class MysqlPipeEnhanceMixin:
    """扩展 mysql pipelines 的功能"""

    @staticmethod
    @retry(
        stop_max_attempt_number=Param.retry_num,
        wait_random_min=Param.retry_time_min,
        wait_random_max=Param.retry_time_max,
    )
    def _connect(mysql_conf: MysqlConf) -> PymysqlConnection:
        """链接数据库操作：
            1.如果链接正常，则返回链接句柄；
            2.如果目标数据库不存在，则创建数据库后再返回链接句柄。

        Args:
            mysql_conf: pymysql 链接所需的参数

        Returns:
            1). mysql 链接句柄
        """
        try:
            conn = MysqlPortal(db_conf=mysql_conf, tag=PortalTag.LIBRARY).connect()
        except Exception as e:
            # (1049, "Unknown database 'xxx'")
            if "1049" in str(e):
                logger.warning(
                    f"目标数据库：{mysql_conf.database} 不存在，尝试创建中..."
                )
                ReuseOperation.create_database(db_conf=mysql_conf)
            else:
                logger.error(f"connect to mysql failed: {e}")
        else:
            return conn
        return MysqlPortal(db_conf=mysql_conf, tag=PortalTag.LIBRARY).connect()

    @staticmethod
    def _get_sql_by_item(
        table: str,
        item: dict[str, Any],
        odku_enable: bool = True,
        insert_prefix: InsertPrefixStr = "INSERT",
    ) -> tuple[str, tuple]:
        """根据处理后的 item 生成 mysql 插入语句

        Args:
            table: 数据库表名
            item: 处理后的 item
            odku_enable: 是否开启 ON DUPLICATE KEY UPDATE
            insert_prefix: INSERT 语句前缀设置: INSERT IGNORE or INSERT

        Returns:
            1). sql 插入语句
            2). sql 语句执行和格式化需要的 value
        """
        keys = f"""`{"`, `".join(item.keys())}`"""
        values = ", ".join(["%s"] * len(item))
        if odku_enable:
            update = ",".join([f" `{key}` = %s" for key in item])
            sql = f"{insert_prefix} INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"
            args = tuple(item.values()) * 2
        else:
            sql = f"{insert_prefix} INTO `{table}` ({keys}) values ({values})"
            args = tuple(item.values())
        return sql, args

    @staticmethod
    def _get_log_by_spider(spider, crawl_time):
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
                            error_reason += (
                                f"{status_code}错误：网页失效/无此网页/网站拒绝访问"
                            )
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
                (_curr_utc_time - stats.get("start_time")).seconds / 60, 2
            ),
            "crawl_time": crawl_time,
        }

        # 错误原因
        if text.get("log_count_ERROR", 0):
            log_info["log_count_ERROR"] = error_reason or "请人工排查错误原因！"

        else:
            log_info["log_count_ERROR"] = ""
        return log_info


class PostgreSQLPipeEnhanceMixin:
    """扩展 postgresql pipelines 的功能"""

    @staticmethod
    @retry(
        stop_max_attempt_number=Param.retry_num,
        wait_random_min=Param.retry_time_min,
        wait_random_max=Param.retry_time_max,
    )
    def _connect(postgres_conf: PostgreSQLConf) -> PsycopgConnection:
        """链接数据库操作：
            1.如果链接正常，则返回链接句柄；
            2.如果目标数据库不存在，则创建数据库后再返回链接句柄。

        Args:
            postgres_conf: postgresql 链接所需的参数

        Returns:
            1). postgresql 链接句柄
        """
        try:
            conn = PostgreSQLPortal(
                db_conf=postgres_conf, tag=PortalTag.LIBRARY
            ).connect()
        except Exception as e:
            # err: connection to server at "x.x.x.x", port x failed: FATAL:  database "x" does not exist
            if "failed" in str(e).lower():
                logger.warning(
                    f"目标数据库：{postgres_conf.database} 不存在，尝试创建中..."
                )
                ReuseOperation.create_database(db_conf=postgres_conf)
            else:
                logger.error(f"connect to postgresql failed: {e}")
        else:
            return conn
        return PostgreSQLPortal(db_conf=postgres_conf, tag=PortalTag.LIBRARY).connect()

    @staticmethod
    def _get_sql_by_item(table: str, item: dict[str, Any]) -> str:
        """根据处理后的 item 生成 postgresql 插入语句

        Args:
            table: 数据库表名
            item: 处理后的 item

        Returns:
            1). sql 插入语句
        """
        keys = f"""{", ".join(item.keys())}"""
        values = ", ".join(["%s"] * len(item))
        return f"INSERT INTO {table} ({keys}) values ({values});"


class OraclePipeEnhanceMixin:
    """扩展 oracle pipelines 的功能"""

    @staticmethod
    @retry(
        stop_max_attempt_number=Param.retry_num,
        wait_random_min=Param.retry_time_min,
        wait_random_max=Param.retry_time_max,
    )
    def _connect(oracle_conf: OracleConf) -> OracleConnection:
        """链接数据库返回链接句柄

        Args:
            oracle_conf: oracle 链接所需的参数

        Returns:
            1). oracle 链接句柄
        """
        return OraclePortal(db_conf=oracle_conf, tag=PortalTag.LIBRARY).connect()

    @staticmethod
    def _get_sql_by_item(table: str, item: dict[str, Any]) -> str:
        """根据处理后的 item 生成 oracle 插入语句

        Args:
            table: 数据库表名
            item: 处理后的 item

        Returns:
            1). sql 插入语句
        """
        keys = f""":{", :".join(item.keys())}"""
        table_keys = ", ".join(map(lambda key: f'"{key}"', item.keys()))
        return f'INSERT INTO "{table}" ({table_keys}) values ({keys})'
