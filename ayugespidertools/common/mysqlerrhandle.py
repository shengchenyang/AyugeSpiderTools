from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

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


class AbstractClass(ABC):
    """用于处理 mysql 异常的模板方法类"""

    def _create_table(
        self,
        cursor: Cursor,
        table_name: str,
        engine: str,
        charset: str,
        collate: str,
        table_notes: str = "",
    ) -> None:
        """创建数据库表

        Args:
            cursor: mysql connect cursor
            table_name: 创建表的名称
            engine: 创建表的 engine
            charset: charset
            collate: collate
            table_notes: 创建表的注释
        """
        sql = (
            f"CREATE TABLE IF NOT EXISTS `{table_name}` (`id` int(32) NOT NULL"
            f" AUTO_INCREMENT COMMENT 'id', PRIMARY KEY (`id`)) ENGINE={engine}"
            f" DEFAULT CHARSET={charset} COLLATE={collate} COMMENT={table_notes!r};"
        )

        try:
            cursor.execute(sql)
            logger.info(f"创建数据表 {table_notes}: {table_name} 成功！")
        except Exception as e:
            logger.error(f"创建表 {table_name} 失败，err：{e}")

    def _get_column_type(
        self,
        cursor: Cursor,
        database: str,
        table: str,
        column: str,
    ) -> str | None:
        """获取数据字段存储类型

        Args:
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            column: 字段名称

        Returns:
            column_type: 字段存储类型
        """
        sql = (
            f"select COLUMN_TYPE from information_schema.columns where table_schema = {database!r}"
            f" and table_name = {table!r} and COLUMN_NAME= {column!r};"
        )
        column_type = None
        try:
            cursor.execute(sql)
            lines = cursor.fetchall()
            if isinstance(lines, list):
                # 此处 AyuMysqlPipeline 返回的结构示例为：[{'COLUMN_TYPE': 'varchar(190)'}]
                column_type = lines[0]["COLUMN_TYPE"] if len(lines) == 1 else ""
            else:
                # 此处 AyuTwistedMysqlPipeline 返回的结构示例为：(('varchar(10)',),)
                column_type = lines[0][0] if len(lines) == 1 else ""

        except Exception as e:
            logger.error(f"未获取到当前字段的存储类型，err: {e}")
        return column_type

    def template_method(
        self,
        err_msg: str,
        conn: Connection,
        cursor: Cursor | TwistedTransactionT,
        mysql_conf: MysqlConf,
        table: str,
        table_notes: str,
        note_dic: dict[str, str],
    ) -> None:
        """模板方法，用于处理 mysql 存储场景的异常

        Args:
            err_msg: pipeline 存储时报错内容
            conn: mysql conn
            cursor: mysql connect cursor
            mysql_conf: spider mysql_conf
            table: 数据表
            table_notes: 数据表注释
            note_dic: 当前表字段注释
        """
        if "1054" in err_msg:
            sql, possible_err = self.deal_1054_error(
                err_msg=err_msg, table=table, note_dic=note_dic
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        elif "1146" in err_msg:
            self._create_table(
                cursor=cursor,
                table_name=table,
                engine=mysql_conf.engine,
                charset=mysql_conf.charset,
                collate=mysql_conf.collate,
                table_notes=table_notes,
            )

        elif "1406" in err_msg:
            sql, possible_err = self.deal_1406_error(
                err_msg=err_msg,
                cursor=cursor,
                database=mysql_conf.database,
                table=table,
                note_dic=note_dic,
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        elif "1265" in err_msg:
            sql, possible_err = self.deal_1265_error(
                err_msg=err_msg,
                cursor=cursor,
                database=mysql_conf.database,
                table=table,
                note_dic=note_dic,
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        else:
            raise Exception(f"MYSQL OTHER ERROR: {err_msg}")

    def deal_1054_error(
        self, err_msg: str, table: str, note_dic: dict[str, str]
    ) -> tuple[str, str]:
        """解决 1054, u"Unknown column 'xx' in 'field list'"

        Args:
            err_msg: 报错内容
            table: 数据表名
            note_dic: 当前表字段的注释

        Returns:
            1). sql: 用于添加字段的 sql 语句
            2). 执行此 sql 可能会报错的信息
        """
        colum_pattern = re.compile(r"Unknown column '(.*?)' in 'field list'")
        text = re.findall(colum_pattern, err_msg)
        colum = text[0]
        notes = note_dic[colum]

        sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` VARCHAR(255) NULL DEFAULT '' COMMENT {notes!r};"
        return sql, f"添加字段 {colum} 已存在"

    def deal_1406_error(
        self,
        err_msg: str,
        cursor: Cursor,
        database: str,
        table: str,
        note_dic: dict[str, str],
    ) -> tuple[str, str]:
        """解决 1406, u"Data too long for 'xx' at ..."

        Args:
            err_msg: 报错内容
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            note_dic: 当前表字段的注释

        Returns:
            1). sql: 修改字段类型的 sql
            2). 执行此 sql 可能会报错的信息
        """
        if "Data too long for" in err_msg:
            colum_pattern = re.compile(r"Data too long for column '(.*?)' at")
            text = re.findall(colum_pattern, err_msg)
            colum = text[0]
            notes = note_dic[colum]
            column_type = self._get_column_type(
                cursor=cursor, database=database, table=table, column=colum
            )
            change_colum_type = "LONGTEXT" if column_type == "text" else "TEXT"
            sql = (
                f"ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}`"
                f" {change_colum_type} NULL DEFAULT NULL COMMENT {notes!r};"
            )
            return sql, f"更新 {colum} 字段类型为 {change_colum_type} 时失败"
        raise Exception(f"未解决 Data too long 的问题，err: {err_msg}")

    def deal_1265_error(
        self,
        err_msg: str,
        cursor: Cursor,
        database: str,
        table: str,
        note_dic: dict[str, str],
    ) -> tuple[str, str]:
        """解决 1265, u"Data truncated for column 'xx' at ..."

        Args:
            err_msg: 报错内容
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            note_dic: 当前表字段的注释

        Returns:
            1). sql: 修改字段类型的 sql
            2). 执行此 sql 可能会报错的信息
        """
        if "Data truncated for column" in err_msg:
            colum_pattern = re.compile(r"Data truncated for column '(.*?)' at")
            text = re.findall(colum_pattern, err_msg)
            colum = text[0]
            notes = note_dic[colum]
            column_type = self._get_column_type(
                cursor=cursor, database=database, table=table, column=colum
            )
            change_colum_type = "LONGTEXT" if column_type == "text" else "TEXT"
            sql = (
                f"ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}`"
                f" {change_colum_type} NULL DEFAULT NULL COMMENT {notes!r};"
            )
            return sql, f"更新 {colum} 字段类型为 {change_colum_type} 时失败"
        raise Exception(f"未解决 Data truncated 问题，err: {err_msg}")

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
        except Exception as e:
            logger.warning(
                f"synchronize mysql exec sql err: {str(e)}\n"
                f"possible_err ->: {possible_err}"
            )


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
        except Exception as e:
            logger.warning(
                f"twisted mysql exec sql err: {str(e)}\n"
                f"possible_err: {possible_err}"
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
    abstract_class.template_method(
        err_msg,
        conn,
        cursor,
        mysql_conf,
        table,
        table_notes,
        note_dic,
    )
