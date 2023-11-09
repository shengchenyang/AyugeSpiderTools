import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple, TypeVar, Union

from ayugespidertools.config import logger

__all__ = [
    "Synchronize",
    "TwistedAsynchronous",
    "deal_mysql_err",
]

if TYPE_CHECKING:
    from pymysql.connections import Connection
    from pymysql.cursors import Cursor, DictCursor

    PymysqlCursorT = TypeVar("PymysqlCursorT", bound=Cursor)
    PymysqlConnectT = TypeVar("PymysqlConnectT", bound=Connection)
    PymysqlDictCursorT = TypeVar("PymysqlDictCursorT", bound=DictCursor)


class AbstractClass(ABC):
    """用于处理 mysql 异常的模板方法类"""

    def _create_table(
        self,
        cursor: Union["PymysqlCursorT", "PymysqlDictCursorT"],
        table_name: str,
        charset: str,
        collate: str,
        table_notes: str = "",
    ) -> None:
        """创建数据库表

        Args:
            cursor: mysql connect cursor，参数选择有：
                1). 类型为 pymysql.cursors.Cursor，在同步 pipelines 中使用；
                2). dbpool.runInteraction() 方法会将数据库连接的游标对象作为参数传入
                回调函数中，而游标对象的类型可能是不同的，比如 DictCursor 或 Cursor 类型，在
                异步 pipelines 中使用；
            table_name: 创建表的名称
            charset: charset
            collate: collate
            table_notes: 创建表的注释
        """
        sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}`
        (`id` int(32) NOT NULL AUTO_INCREMENT COMMENT 'id', PRIMARY KEY (`id`))
        ENGINE=InnoDB DEFAULT CHARSET={charset} COLLATE={collate} COMMENT='{table_notes}';
        """

        try:
            # 执行 sql 查询，获取数据
            data = cursor.execute(sql)
            if any([data == 0, not data]):
                logger.info(f"创建数据表 {table_notes}: {table_name} 成功！")

        except Exception as e:
            logger.error(
                f"创建表失败，table_notes：{table_notes}，table_name：{table_name}，error：{e}"
            )

    def _get_column_type(
        self,
        cursor: Union["PymysqlCursorT", "PymysqlDictCursorT"],
        database: str,
        table: str,
        column: str,
    ) -> Union[str, None]:
        """获取数据字段存储类型

        Args:
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            column: 字段名称

        Returns:
            column_type: 字段存储类型
        """
        sql = f"""
        select COLUMN_TYPE from information_schema.columns
        where table_schema = '{database}' and table_name = '{table}' and COLUMN_NAME= '{column}';
        """
        column_type = None
        try:
            if _ := cursor.execute(sql):
                lines = cursor.fetchall()
                if isinstance(lines, list):
                    # 注意，此处 AyuMysqlPipeline 返回的结构示例为：[{'COLUMN_TYPE': 'varchar(190)'}]
                    column_type = lines[0]["COLUMN_TYPE"] if len(lines) == 1 else ""
                else:
                    # 注意，此处 AyuTwistedMysqlPipeline 返回的结构示例为：(('varchar(10)',),)
                    column_type = lines[0][0] if len(lines) == 1 else ""

        except Exception as e:
            logger.error(f"{e}")
        return column_type

    def template_method(
        self,
        err_msg: str,
        conn: "PymysqlConnectT",
        cursor: Union["PymysqlCursorT", "PymysqlDictCursorT"],
        charset: str,
        collate: str,
        database: str,
        table: str,
        table_notes: str,
        note_dic: dict,
    ) -> None:
        """模板方法，用于处理 mysql 存储场景的异常

        Args:
            err_msg: pipeline 存储时报错内容
            conn: mysql conn
            cursor: mysql connect cursor
            charset: mysql table charset
            collate: mysql table collate
            database: 数据库
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
                charset=charset,
                collate=collate,
                table_notes=table_notes,
            )

        elif "1406" in err_msg:
            sql, possible_err = self.deal_1406_error(
                err_msg=err_msg,
                cursor=cursor,
                database=database,
                table=table,
                note_dic=note_dic,
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        elif "1265" in err_msg:
            sql, possible_err = self.deal_1265_error(
                err_msg=err_msg,
                cursor=cursor,
                database=database,
                table=table,
                note_dic=note_dic,
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        else:
            # 碰到其他的异常才打印错误日志，已处理的异常不打印
            logger.error(f"ERROR: {err_msg}")

    def deal_1054_error(
        self, err_msg: str, table: str, note_dic: dict
    ) -> Tuple[str, str]:
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

        sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` VARCHAR(190) NULL DEFAULT '' COMMENT '{notes}';"
        return sql, f"1054: 添加字段 {colum} 已存在"

    def deal_1406_error(
        self,
        err_msg: str,
        cursor: Union["PymysqlCursorT", "PymysqlDictCursorT"],
        database: str,
        table: str,
        note_dic: dict,
    ) -> Tuple[str, str]:
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
            sql = f"""
            ALTER TABLE `{table}` CHANGE COLUMN
            `{colum}` `{colum}` {change_colum_type} NULL DEFAULT NULL COMMENT "{notes}";
            """
            return sql, f"1406: 更新 {colum} 字段类型为 {change_colum_type} 时失败"

    def deal_1265_error(
        self,
        err_msg: str,
        cursor: Union["PymysqlCursorT", "PymysqlDictCursorT"],
        database: str,
        table: str,
        note_dic: dict,
    ) -> Tuple[str, str]:
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
            sql = f"""
            ALTER TABLE `{table}` CHANGE COLUMN
            `{colum}` `{colum}` {change_colum_type} NULL DEFAULT NULL COMMENT "{notes}";
            """
            return sql, f"1265: 更新 {colum} 字段类型为 {change_colum_type} 时失败"

    @abstractmethod
    def _exec_sql(self, *args, **kwargs) -> None:
        """子类要实现执行 sql 的不同方法，使得可以正常适配不同的 pipelines 场景"""
        pass


class Synchronize(AbstractClass):
    """pipeline 同步执行 sql 的场景"""

    def _exec_sql(
        self,
        conn: "PymysqlConnectT",
        cursor: "PymysqlCursorT",
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
        cursor: "PymysqlDictCursorT",
        sql: str,
        possible_err: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        try:
            cursor.execute(sql)
        except Exception as e:
            if possible_err:
                logger.info(f"{possible_err}")
            else:
                logger.info(f"{e}")


def deal_mysql_err(
    abstract_class: AbstractClass,
    err_msg: str,
    cursor: Union["PymysqlCursorT", "PymysqlDictCursorT"],
    charset: str,
    collate: str,
    database: str,
    table: str,
    table_notes: str,
    note_dic: dict,
    conn: Optional["PymysqlConnectT"] = None,
) -> None:
    abstract_class.template_method(
        err_msg,
        conn,
        cursor,
        charset,
        collate,
        database,
        table,
        table_notes,
        note_dic,
    )
