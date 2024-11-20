from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from ayugespidertools.config import logger

__all__ = [
    "Synchronize",
    "deal_postgres_err",
    "TwistedAsynchronous",
]

if TYPE_CHECKING:
    from psycopg.connection import Connection
    from psycopg.cursor import Cursor
    from twisted.enterprise.adbapi import Transaction

    TwistedTransactionT = TypeVar("TwistedTransactionT", bound=Transaction)


class AbstractClass(ABC):
    """用于处理 postgresql 异常的模板方法类"""

    def template_method(
        self,
        err_msg: str,
        conn: Connection,
        cursor: Cursor | TwistedTransactionT,
        table: str,
        table_notes: str,
        note_dic: dict[str, str],
    ) -> None:
        """模板方法，用于处理 postgresql 存储场景的异常

        Args:
            err_msg: pipeline 存储时报错内容
            conn: postgresql conn
            cursor: postgresql connect cursor or twisted.enterprise.adbapi.Transaction
            table: 数据表
            table_notes: 数据表注释
            note_dic: 当前表字段注释
        """
        if f' of relation "{table}" does not exist' in err_msg:
            sql, possible_err = self.deal_1054_error(
                err_msg=err_msg, table=table, note_dic=note_dic
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        elif f'relation "{table}" does not exist' in err_msg:
            sql = f"""
            CREATE TABLE IF NOT EXISTS {table} (id SERIAL NOT NULL PRIMARY KEY);
            COMMENT ON TABLE {table} IS {table_notes!r};
            COMMENT ON COLUMN {table}.id IS 'id';
            """
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err="创建表失败")

        elif "value too long for type" in err_msg:
            raise Exception(f"postgres 有字段超出长度限制：{err_msg}")

        else:
            raise Exception(f"POSTGRES OTHER ERROR: {err_msg}")

    def deal_1054_error(
        self, err_msg: str, table: str, note_dic: dict[str, str]
    ) -> tuple[str, str]:
        """解决 column "xxx" of relation "x" does not exist

        Args:
            err_msg: 报错内容
            table: 数据表名
            note_dic: 当前表字段的注释

        Returns:
            1). sql: 用于添加字段的 sql 语句
            2). 执行此 sql 可能会报错的信息
        """
        colum_pattern = re.compile(r'column "(.*?)" of relation ".*?" does not exist')
        text = re.findall(colum_pattern, err_msg)
        colum = text[0]
        notes = note_dic[colum]

        sql = (
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {colum} VARCHAR(255) DEFAULT '';"
            f"COMMENT ON COLUMN {table}.{colum} IS {notes!r}"
        )
        return sql, f"添加字段 {colum} 已存在"

    @abstractmethod
    def _exec_sql(self, *args, **kwargs) -> None:
        """子类要实现执行 sql 的不同方法，使得可以正常适配不同的 pipelines 场景"""
        raise NotImplementedError("Subclasses must implement the '_exec_sql' method")


class Synchronize(AbstractClass):
    """pipeline 同步执行 sql 的场景"""

    def _exec_sql(
        self,
        conn: Connection,
        cursor: Cursor,
        sql: str,
        possible_err: str | None = None,
        *args,
        **kwargs,
    ) -> None:
        try:
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            logger.warning(
                f"synchronize postgres exec sql err: {str(e)}\n"
                f"possible_err: {possible_err}"
            )
            conn.rollback()


class TwistedAsynchronous(AbstractClass):
    """pipeline twisted 异步执行 sql 的场景"""

    def _exec_sql(
        self,
        cursor: TwistedTransactionT,
        sql: str,
        possible_err: str | None = None,
        *args,
        **kwargs,
    ) -> None:
        try:
            cursor.execute(sql)
            cursor.execute("COMMIT")
        except Exception as e:
            logger.warning(
                f"twisted postgres exec sql err: {str(e)}\n"
                f"possible_err ->: {possible_err}"
            )
            cursor.execute("ROLLBACK")


def deal_postgres_err(
    abstract_class: AbstractClass,
    err_msg: str,
    cursor: Cursor | TwistedTransactionT,
    table: str,
    table_notes: str,
    note_dic: dict[str, str],
    conn: Connection | None = None,
) -> None:
    abstract_class.template_method(
        err_msg,
        conn,
        cursor,
        table,
        table_notes,
        note_dic,
    )
