from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple, TypeVar

from ayugespidertools.config import logger

__all__ = [
    "Synchronize",
    "TwistedAsynchronous",
    "deal_postgres_err",
]

if TYPE_CHECKING:
    from psycopg.connection import Connection
    from psycopg.cursor import Cursor
    from twisted.enterprise.adbapi import Transaction

    TwistedTransactionT = TypeVar("TwistedTransactionT", bound=Transaction)


class PostgresContext(NamedTuple):
    cursor: Cursor | Transaction
    conn: Connection | None = None


class AbstractClass(ABC):
    """Template method base class for recovering from PostgreSQL pipeline errors."""

    def template_method(
        self,
        err_msg: str,
        context: PostgresContext,
        table: str,
        table_notes: str,
        note_dic: dict[str, str],
    ) -> None:
        """Handle exceptions encountered during PostgreSQL storage operations.

        Args:
            err_msg: Error message raised while storing an item.
            context: PostgreSQL cursor and optional connection.
            table: Destination table name.
            table_notes: Database table comment.
            note_dic: Mapping of column names to database column comments.
        """
        table = table.rsplit(".", 1)[-1]
        if f' of relation "{table}" does not exist' in err_msg:
            sql, possible_err = self.deal_1054_error(
                err_msg=err_msg, table=table, note_dic=note_dic
            )
            self._exec_sql(context=context, sql=sql, possible_err=possible_err)

        elif f'relation "{table}" does not exist' in err_msg:
            sql = f"""
            CREATE TABLE IF NOT EXISTS {table} (id SERIAL NOT NULL PRIMARY KEY);
            COMMENT ON TABLE {table} IS {table_notes!r};
            COMMENT ON COLUMN {table}.id IS 'id';
            """
            self._exec_sql(
                context=context,
                sql=sql,
                possible_err="Failed to create the PostgreSQL table",
            )

        elif "value too long for type" in err_msg:
            raise Exception(
                f"A PostgreSQL column value exceeds its length limit: {err_msg}"
            )

        else:
            raise Exception(f"Unhandled PostgreSQL error: {err_msg}")

    def deal_1054_error(
        self, err_msg: str, table: str, note_dic: dict[str, str]
    ) -> tuple[str, str]:
        """Example error message: column "xxx" of relation "x" does not exist"""
        colum_pattern = re.compile(r'column "(.*?)" of relation ".*?" does not exist')
        text = re.findall(colum_pattern, err_msg)
        colum = text[0]
        notes = note_dic[colum]

        sql = (
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {colum} VARCHAR(255) DEFAULT '';"
            f"COMMENT ON COLUMN {table}.{colum} IS {notes!r}"
        )
        return sql, f"Failed to add column {colum}; the column may already exist"

    @abstractmethod
    def _exec_sql(
        self, context: PostgresContext, sql: str, possible_err: str | None = None
    ) -> None:
        raise NotImplementedError("Subclasses must implement the '_exec_sql' method")


class Synchronize(AbstractClass):
    """Execute PostgreSQL recovery SQL synchronously."""

    def _exec_sql(
        self, context: PostgresContext, sql: str, possible_err: str | None = None
    ) -> None:
        assert context.conn is not None
        try:
            context.cursor.execute(sql)  # type: ignore[arg-type]
            context.conn.commit()
        except Exception as e:
            logger.warning(
                f"Synchronous PostgreSQL recovery SQL execution failed: {e!s}\n"
                f"Recovery context: {possible_err}"
            )
            context.conn.rollback()


class TwistedAsynchronous(AbstractClass):
    """Execute PostgreSQL recovery SQL in a Twisted pipeline transaction."""

    def _exec_sql(
        self, context: PostgresContext, sql: str, possible_err: str | None = None
    ) -> None:
        try:
            context.cursor.execute(sql)  # type: ignore[arg-type]
            context.cursor.execute("COMMIT")
        except Exception as e:
            logger.warning(
                f"Twisted PostgreSQL recovery SQL execution failed: {e!s}\n"
                f"Recovery context: {possible_err}"
            )
            context.cursor.execute("ROLLBACK")


def deal_postgres_err(
    abstract_class: AbstractClass,
    err_msg: str,
    cursor: Cursor | TwistedTransactionT,
    table: str,
    table_notes: str,
    note_dic: dict[str, str],
    conn: Connection | None = None,
) -> None:
    context = PostgresContext(cursor=cursor, conn=conn)
    abstract_class.template_method(
        err_msg,
        context,
        table,
        table_notes,
        note_dic,
    )
