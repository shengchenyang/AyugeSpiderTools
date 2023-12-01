import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple, TypeVar, Union

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
    PsycopgConnectT = TypeVar("PsycopgConnectT", bound=Connection)
    PsycopgCursorT = TypeVar("PsycopgCursorT", bound=Cursor)


class AbstractClass(ABC):
    """用于处理 postgresql 异常的模板方法类"""

    def template_method(
        self,
        err_msg: str,
        conn: "PsycopgConnectT",
        cursor: Union["PsycopgCursorT", "TwistedTransactionT"],
        table: str,
        table_notes: str,
        note_dic: dict,
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
            COMMENT ON TABLE {table} IS '{table_notes}';
            COMMENT ON COLUMN {table}.id IS 'id';
            """
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err="创建表失败")

        elif "value too long for type" in err_msg:
            raise Exception(f"postgres 有字段超出长度限制：{err_msg}")

        else:
            # 碰到其他的异常才打印错误日志，已处理的异常不打印
            logger.error(f"ERROR: {err_msg}")

    def deal_1054_error(
        self, err_msg: str, table: str, note_dic: dict
    ) -> Tuple[str, str]:
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
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {colum} VARCHAR(190) DEFAULT '';"
            f"COMMENT ON COLUMN {table}.{colum} IS '{notes}'"
        )
        return sql, f"添加字段 {colum} 已存在"

    @abstractmethod
    def _exec_sql(self, *args, **kwargs) -> None:
        """子类要实现执行 sql 的不同方法，使得可以正常适配不同的 pipelines 场景"""
        pass


class Synchronize(AbstractClass):
    """pipeline 同步执行 sql 的场景"""

    def _exec_sql(
        self,
        conn: "PsycopgConnectT",
        cursor: "PsycopgCursorT",
        sql: str,
        possible_err: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        try:
            if cursor.execute(sql):
                conn.commit()
        except Exception as e:
            if possible_err:
                logger.info(f"{possible_err}")
            else:
                logger.info(f"{e}")


class TwistedAsynchronous(AbstractClass):
    """pipeline twisted 异步执行 sql 的场景"""

    def _exec_sql(
        self,
        cursor: "TwistedTransactionT",
        sql: str,
        possible_err: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        try:
            cursor.execute(sql)
            cursor.execute("COMMIT")
        except Exception as e:
            if possible_err:
                logger.info(f"{possible_err}: {str(e)}")
                cursor.execute("ROLLBACK")
                cursor.execute(sql)
            else:
                logger.info(f"{e}")


def deal_postgres_err(
    abstract_class: AbstractClass,
    err_msg: str,
    cursor: Union["PsycopgCursorT", "TwistedTransactionT"],
    table: str,
    table_notes: str,
    note_dic: dict,
    conn: Optional["PsycopgConnectT"] = None,
) -> None:
    abstract_class.template_method(
        err_msg,
        conn,
        cursor,
        table,
        table_notes,
        note_dic,
    )
