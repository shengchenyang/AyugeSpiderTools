from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.typevars import InsertPrefixStr, PortalTag
from ayugespidertools.config import logger
from ayugespidertools.utils.database import MysqlPortal, OraclePortal, PostgreSQLPortal

__all__ = [
    "MysqlPipeEnhanceMixin",
    "OraclePipeEnhanceMixin",
    "PostgreSQLPipeEnhanceMixin",
]

if TYPE_CHECKING:
    from oracledb.connection import Connection as OracleConnection
    from psycopg.connection import Connection as PsycopgConnection
    from pymysql.connections import Connection as PymysqlConnection

    from ayugespidertools.common.typevars import MysqlConf, OracleConf, PostgreSQLConf


class MysqlPipeEnhanceMixin:
    @staticmethod
    def _connect(mysql_conf: MysqlConf) -> PymysqlConnection:
        """Connect to MySQL, creating the database if it does not exist.

        Args:
            mysql_conf: MySQL connection configure.

        Returns:
            A PyMySQL connection.
        """
        try:
            conn = MysqlPortal(db_conf=mysql_conf, tag=PortalTag.LIBRARY).connect()
        except Exception as e:
            # (1049, "Unknown database 'xxx'")
            if "1049" in str(e):
                logger.warning(
                    f"MySQL database {mysql_conf.database} does not exist; "
                    "attempting to create it ..."
                )
                ReuseOperation.create_database(db_conf=mysql_conf)
            else:
                logger.error(f"Failed to connect to MySQL: {e}")
        else:
            return conn
        return MysqlPortal(db_conf=mysql_conf, tag=PortalTag.LIBRARY).connect()

    @staticmethod
    def _get_sql_by_item(
        table: str,
        item: dict[str, Any],
        odku_enable: bool = True,
        insert_prefix: InsertPrefixStr = "INSERT",
        duplicate: dict[str, Any] | None = None,
    ) -> tuple[str, tuple]:
        """Build a parameterized MySQL INSERT statement for an item.

        Args:
            table: Destination table name.
            item: Processed item containing column names and values.
            odku_enable: Whether to allow an ON DUPLICATE KEY UPDATE clause.
            insert_prefix: INSERT statement prefix, either "INSERT" or "INSERT IGNORE".
            duplicate: Columns and values to update on a duplicate key. An update
                clause is added only when odku_enable and duplicate are both truthy.

        Returns:
            The SQL statement and a tuple of bound parameter values.
        """
        keys = f"""`{"`, `".join(item.keys())}`"""
        values = ", ".join(["%s"] * len(item))
        if odku_enable:
            if duplicate:
                update = ",".join([f" `{key}` = %s" for key in duplicate])
                args = tuple(item.values()) + tuple(duplicate.values())
                sql = f"{insert_prefix} INTO `{table}` ({keys}) values ({values}) ON DUPLICATE KEY UPDATE {update}"
            else:
                args = tuple(item.values())
                sql = f"{insert_prefix} INTO `{table}` ({keys}) values ({values})"
            return sql, args
        sql = f"{insert_prefix} INTO `{table}` ({keys}) values ({values})"
        args = tuple(item.values())
        return sql, args

    @staticmethod
    def _get_log_by_spider(spider, crawl_time):
        """Summarize a spider run using Scrapy statistics.

        Args:
            spider: Scrapy spider with MySQL configuration.
            crawl_time: Crawl date recorded with the statistics.

        Returns:
            A dictionary of run statistics and diagnostic error descriptions.
        """
        mysql_conf = spider.mysql_conf
        text: dict[str, Any] = {}
        stats = spider.crawler.stats.get_stats()
        error_reason = ""
        _curr_utc_time = datetime.datetime.now(datetime.UTC)
        for k, v in stats.items():
            key = k.replace("/", "_")
            if isinstance(v, datetime.datetime):
                text[key] = (v + datetime.timedelta(hours=8)).strftime(
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
                            error_reason += (
                                f"HTTP {status_code}: request rate limit exceeded; "
                            )
                        else:
                            error_reason += f"HTTP {status_code}: client error; the resource may be unavailable or access denied; "
                    elif status_code.startswith("5"):
                        error_reason += f"HTTP {status_code}: server error; "
                    elif status_code != "":
                        error_reason += (
                            f"HTTP {status_code}: manual investigation required; "
                        )
                elif "exception_type_count" in k:
                    error_name = k.split("/")[-1]
                    if "Timeout" in error_name:
                        error_reason += f"{error_name}: response timed out; "
                    elif "ConnectionDone" in error_name:
                        error_reason += f"{error_name}: connection closed; "
                    else:
                        # "ResponseNeverReceived" or "ResponseFailed"
                        error_reason += (
                            f"{error_name}: request failed without a usable response; "
                        )
                text[key] = v

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

        if text.get("log_count_ERROR", 0):
            log_info["log_count_ERROR"] = (
                error_reason
                or "Manual investigation required to determine the cause of the errors"
            )

        else:
            log_info["log_count_ERROR"] = ""
        return log_info


class PostgreSQLPipeEnhanceMixin:
    @staticmethod
    def _connect(postgres_conf: PostgreSQLConf) -> PsycopgConnection:
        """Connect to PostgreSQL and attempt database creation on matching connection errors.

        Args:
            postgres_conf: PostgreSQL connection configure.

        Returns:
            A psycopg connection.
        """
        try:
            conn = PostgreSQLPortal(
                db_conf=postgres_conf, tag=PortalTag.LIBRARY
            ).connect()
        except Exception as e:
            # err: connection to server at "x.x.x.x", port x failed: FATAL:  database "x" does not exist
            if "failed" in str(e).lower():
                logger.warning(
                    f"PostgreSQL database {postgres_conf.database} does not exist; "
                    "attempting to create it ..."
                )
                ReuseOperation.create_database(db_conf=postgres_conf)
            else:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
        else:
            return conn
        return PostgreSQLPortal(db_conf=postgres_conf, tag=PortalTag.LIBRARY).connect()

    @staticmethod
    def _get_sql_by_item(
        table: str, item: dict[str, Any], is_psycopg: bool = False
    ) -> str:
        """Build a parameterized PostgreSQL INSERT statement for an item.

        Args:
            table: Destination table name.
            item: Processed item containing column names and values.
            is_psycopg: Use psycopg placeholders when True; otherwise use asyncpg
                placeholders and append ON CONFLICT DO NOTHING.

        Returns:
            The SQL INSERT statement.
        """
        if is_psycopg:
            keys = f"""{", ".join(item.keys())}"""
            values = ", ".join(["%s"] * len(item))
            return f"INSERT INTO {table} ({keys}) values ({values});"
        keys = ", ".join(item.keys())
        values = ", ".join(f"${i}" for i in range(1, len(item) + 1))
        return f"INSERT INTO {table} ({keys}) VALUES ({values}) ON CONFLICT DO NOTHING;"


class OraclePipeEnhanceMixin:
    @staticmethod
    def _connect(oracle_conf: OracleConf) -> OracleConnection:
        """Open an Oracle database connection.

        Args:
            oracle_conf: Oracle connection configure.

        Returns:
            An Oracle connection.
        """
        return OraclePortal(db_conf=oracle_conf, tag=PortalTag.LIBRARY).connect()

    @staticmethod
    def _get_sql_by_item(table: str, item: dict[str, Any]) -> str:
        """Build an Oracle INSERT statement with named bind parameters.

        Args:
            table: Destination table name.
            item: Processed item containing column names and values.

        Returns:
            The SQL INSERT statement.
        """
        keys = f""":{", :".join(item.keys())}"""
        table_keys = ", ".join(f'"{key}"' for key in item)
        return f'INSERT INTO "{table}" ({table_keys}) values ({keys})'
