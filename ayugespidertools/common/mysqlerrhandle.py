from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple, TypeVar

from ayugespidertools.config import logger

__all__ = [
    "Synchronize",
    "TwistedAsynchronous",
    "deal_mysql_err",
]

if TYPE_CHECKING:
    from pymysql.connections import Connection
    from pymysql.cursors import Cursor, DictCursor
    from twisted.enterprise.adbapi import Transaction

    from ayugespidertools.common.typevars import MysqlConf

    TwistedTransactionT = TypeVar("TwistedTransactionT", bound=Transaction)
    PymysqlDictCursorT = TypeVar("PymysqlDictCursorT", bound=DictCursor)


class MysqlContext(NamedTuple):
    cursor: Cursor | Transaction
    conn: Connection | None = None


class AbstractClass(ABC):
    """Template method base class for recovering from MySQL pipeline errors."""

    def _create_table(
        self,
        context: MysqlContext,
        table_name: str,
        engine: str,
        charset: str,
        collate: str,
        table_notes: str = "",
    ) -> None:
        """Create a MySQL table with an auto-incrementing primary key.

        Args:
            context: MySQL cursor and optional connection.
            table_name: Name of the table to create.
            engine: MySQL storage engine.
            charset: Table character set.
            collate: Table collation.
            table_notes: Database table comment.
        """
        sql = (
            f"CREATE TABLE IF NOT EXISTS `{table_name}` (`id` int(32) NOT NULL"
            f" AUTO_INCREMENT COMMENT 'id', PRIMARY KEY (`id`)) ENGINE={engine}"
            f" DEFAULT CHARSET={charset} COLLATE={collate} COMMENT={table_notes!r};"
        )

        try:
            context.cursor.execute(sql)
            logger.info(
                f"Created MySQL table {table_name} ({table_notes}) successfully"
            )
        except Exception as e:
            logger.error(f"Failed to create MySQL table {table_name}: {e}")

    def _get_column_type(
        self, context: MysqlContext, database: str, table: str, column: str
    ) -> str | None:
        """Look up a column type in the MySQL information schema.

        Args:
            context: MySQL cursor and optional connection.
            database: Database name.
            table: Table name.
            column: Column name.

        Returns:
            The column type, an empty string for an unexpected row count,
            or None if the query fails.
        """
        sql = (
            f"select COLUMN_TYPE from information_schema.columns where table_schema = {database!r}"
            f" and table_name = {table!r} and COLUMN_NAME= {column!r};"
        )
        column_type = None
        try:
            context.cursor.execute(sql)
            lines = context.cursor.fetchall()
            if isinstance(lines, list):
                # AyuMysqlPipeline uses a dictionary cursor, e.g. [{'COLUMN_TYPE': 'varchar(190)'}]
                column_type = lines[0]["COLUMN_TYPE"] if len(lines) == 1 else ""
            else:
                # AyuTwistedMysqlPipeline uses a tuple cursor, e.g. (('varchar(10)',),)
                column_type = lines[0][0] if len(lines) == 1 else ""

        except Exception as e:
            logger.error(f"Failed to retrieve the column type: {e}")
        return column_type

    def template_method(
        self,
        err_msg: str,
        context: MysqlContext,
        mysql_conf: MysqlConf,
        table: str,
        table_notes: str,
        note_dic: dict[str, str],
    ) -> None:
        """Handle exceptions encountered during MySQL storage operations.

        Args:
            err_msg: Error message raised while storing an item.
            context: MySQL connection.
            mysql_conf: Spider mysql connection configure.
            table: Destination table name.
            table_notes: Database table comment.
            note_dic: Mapping of column names to database column comments.
        """
        if "1054" in err_msg:
            sql, possible_err = self.deal_1054_error(
                err_msg=err_msg, table=table, note_dic=note_dic
            )
            self._exec_sql(context=context, sql=sql, possible_err=possible_err)

        elif "1146" in err_msg:
            self._create_table(
                context=context,
                table_name=table,
                engine=mysql_conf.engine,
                charset=mysql_conf.charset,
                collate=mysql_conf.collate,
                table_notes=table_notes,
            )

        elif "1406" in err_msg:
            sql, possible_err = self.deal_1406_error(
                err_msg=err_msg,
                context=context,
                database=mysql_conf.database,
                table=table,
                note_dic=note_dic,
            )
            self._exec_sql(context=context, sql=sql, possible_err=possible_err)

        elif "1265" in err_msg:
            sql, possible_err = self.deal_1265_error(
                err_msg=err_msg,
                context=context,
                database=mysql_conf.database,
                table=table,
                note_dic=note_dic,
            )
            self._exec_sql(context=context, sql=sql, possible_err=possible_err)

        else:
            raise Exception(f"Unhandled MySQL error: {err_msg}")

    def deal_1054_error(
        self, err_msg: str, table: str, note_dic: dict[str, str]
    ) -> tuple[str, str]:
        """Handle MySQL error 1054.

        Example error message: u"Unknown column 'xx' in 'field list'"
        """
        colum_pattern = re.compile(r"Unknown column '(.*?)' in 'field list'")
        text = re.findall(colum_pattern, err_msg)
        colum = text[0]
        notes = note_dic[colum]

        sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` VARCHAR(255) NULL DEFAULT '' COMMENT {notes!r};"
        return sql, f"Failed to add column {colum}; the column may already exist"

    def deal_1406_error(
        self,
        err_msg: str,
        context: MysqlContext,
        database: str,
        table: str,
        note_dic: dict[str, str],
    ) -> tuple[str, str]:
        """Handle MySQL error 1406.

        Example error message: u"Data too long for 'xx' at ..."
        """
        if "Data too long for" in err_msg:
            colum_pattern = re.compile(r"Data too long for column '(.*?)' at")
            text = re.findall(colum_pattern, err_msg)
            colum = text[0]
            notes = note_dic[colum]
            column_type = self._get_column_type(
                context=context, database=database, table=table, column=colum
            )
            change_colum_type = "LONGTEXT" if column_type == "text" else "TEXT"
            sql = (
                f"ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}`"
                f" {change_colum_type} NULL DEFAULT NULL COMMENT {notes!r};"
            )
            return sql, f"Failed to change column {colum} to {change_colum_type}"
        raise Exception(f"Unable to recover from the data-too-long error: {err_msg}")

    def deal_1265_error(
        self,
        err_msg: str,
        context: MysqlContext,
        database: str,
        table: str,
        note_dic: dict[str, str],
    ) -> tuple[str, str]:
        """Handle MySQL error 1265.

        Example error message: u"Data truncated for column 'xx' at ..."
        """
        if "Data truncated for column" in err_msg:
            colum_pattern = re.compile(r"Data truncated for column '(.*?)' at")
            text = re.findall(colum_pattern, err_msg)
            colum = text[0]
            notes = note_dic[colum]
            column_type = self._get_column_type(
                context=context, database=database, table=table, column=colum
            )
            change_colum_type = "LONGTEXT" if column_type == "text" else "TEXT"
            sql = (
                f"ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}`"
                f" {change_colum_type} NULL DEFAULT NULL COMMENT {notes!r};"
            )
            return sql, f"Failed to change column {colum} to {change_colum_type}"
        raise Exception(f"Failed to resolve the Data truncated issue. Error: {err_msg}")

    @abstractmethod
    def _exec_sql(
        self, context: MysqlContext, sql: str, possible_err: str | None = None
    ) -> None:
        raise NotImplementedError("Subclasses must implement the '_exec_sql' method")


class Synchronize(AbstractClass):
    """Execute MySQL recovery SQL synchronously."""

    def _exec_sql(
        self, context: MysqlContext, sql: str, possible_err: str | None = None
    ) -> None:
        try:
            context.cursor.execute(sql)
        except Exception as e:
            logger.warning(
                f"Synchronous MySQL recovery SQL execution failed: {e!s}\n"
                f"Recovery context: {possible_err}"
            )


class TwistedAsynchronous(AbstractClass):
    """Execute MySQL recovery SQL in a Twisted pipeline transaction."""

    def _exec_sql(
        self, context: MysqlContext, sql: str, possible_err: str | None = None
    ) -> None:
        try:
            context.cursor.execute(sql)
        except Exception as e:
            logger.warning(
                f"Twisted MySQL recovery SQL execution failed: {e!s}\n"
                f"Recovery context: {possible_err}"
            )


def deal_mysql_err(
    abstract_class: AbstractClass,
    err_msg: str,
    cursor: Cursor | TwistedTransactionT,
    mysql_conf: MysqlConf,
    table: str,
    table_notes: str,
    note_dic: dict[str, str],
    conn: Connection | None = None,
) -> None:
    context = MysqlContext(cursor=cursor, conn=conn)
    abstract_class.template_method(
        err_msg,
        context,
        mysql_conf,
        table,
        table_notes,
        note_dic,
    )
