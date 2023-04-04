import re
from abc import ABC, abstractmethod
from typing import Optional, Type, Union

from ayugespidertools.common.Params import Param
from ayugespidertools.common.TypeVars import TableEnumTypeVar
from ayugespidertools.config import logger

__all__ = [
    "Synchronize",
    "TwistedAsynchronous",
    "deal_mysql_err",
]


class AbstractClass(ABC):
    """
    用于处理 mysql 异常的模板方法类
    """

    def _create_table(
        self,
        cursor: Union[Param.PymysqlCursor, Param.PymysqlDictCursor],
        table_name: str,
        charset: str,
        collate: str,
        tabel_notes: str = "",
        demand_code: str = "",
    ) -> None:
        """
        创建数据库表
        Args:
            cursor: mysql connect cursor，参数选择有：
                1). 类型为 pymysql.cursors.Cursor，在同步 pipelines 中使用；
                2). dbpool.runInteraction() 方法会将数据库连接的游标对象作为参数传入
                回调函数中，而游标对象的类型可能是不同的，比如 DictCursor 或 Cursor 类型，在
                异步 pipelines 中使用；
            table_name: 创建表的名称
            charset: charset
            collate: collate
            tabel_notes: 创建表的注释
            demand_code: 创建表的需求对应的 code 值，用于和需求中的任务对应

        Returns:
            None
        """
        # 用于表格 comment 的参数生成(即 tabel_notes 参数)
        if demand_code != "":
            tabel_notes = f"{demand_code}_{tabel_notes}"

        sql = f"""CREATE TABLE IF NOT EXISTS `{table_name}` (`id` int(32) NOT NULL AUTO_INCREMENT COMMENT 'id',
            PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET={charset} 
            COLLATE={collate} COMMENT='{tabel_notes}'; """
        try:
            # 执行 sql 查询，获取数据
            data = cursor.execute(sql)
            if any([data == 0, not data]):
                logger.info(f"创建数据表 {tabel_notes}: {table_name} 成功！")

        except Exception as e:
            logger.error(
                f"创建表失败，tabel_notes：{tabel_notes}，table_name：{table_name}，error：{e}"
            )

    def _get_column_type(
        self,
        cursor: Union[Param.PymysqlCursor, Param.PymysqlDictCursor],
        database: str,
        table: str,
        column: str,
    ) -> str:
        """
        获取数据字段存储类型
        Args:
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            column: 字段名称

        Returns:
            column_type: 字段存储类型
        """
        sql = f"""select COLUMN_TYPE from information_schema.columns where table_schema = '{database}' and 
            table_name = '{table}' and COLUMN_NAME= '{column}';"""
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
        conn: Param.PymysqlConnect,
        cursor: Union[Param.PymysqlCursor, Param.PymysqlDictCursor],
        charset: str,
        collate: str,
        database: str,
        table: str,
        table_prefix: str,
        table_enum: Type[TableEnumTypeVar],
        note_dic: dict,
    ) -> None:
        """
        模板方法，用于处理 mysql 存储场景的异常
        Args:
            err_msg: pipeline 存储时报错内容
            conn: mysql conn
            cursor: mysql connect cursor
            charset: mysql table charset
            collate: mysql table collate
            database: 数据库
            table: 数据表
            table_prefix: 数据表前缀
            table_enum: 数据表枚举类
            note_dic: 当前表字段注释

        Returns:
            None
        """
        if "1054" in err_msg:
            sql, possible_err = self.deal_1054_error(
                err_msg=err_msg, table=table, note_dic=note_dic
            )
            self._exec_sql(conn=conn, cursor=cursor, sql=sql, possible_err=possible_err)

        elif "1146" in err_msg:
            table_name, table_notes, demand_code = self.deal_1146_error(
                err_msg=err_msg,
                table_prefix=table_prefix,
                table_enum=table_enum,
            )
            self._create_table(
                cursor=cursor,
                table_name=table_name,
                charset=charset,
                collate=collate,
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

    def deal_1054_error(self, err_msg: str, table: str, note_dic: dict) -> (str, str):
        """
        解决 1054, u"Unknown column 'id' in 'field list'"
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

        if colum == "url":
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` TEXT(500) NULL COMMENT '{notes}';"
        elif colum in {"create_time", "crawl_time", "update_time"}:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` DATE NULL DEFAULT NULL COMMENT '{notes}';"
        else:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` VARCHAR(190) NULL DEFAULT '' COMMENT '{notes}';"
        return sql, f"1054: 添加字段 {colum} 已存在"

    def deal_1146_error(
        self,
        err_msg: str,
        table_prefix: str,
        table_enum: Type[TableEnumTypeVar],
    ) -> (str, str, str):
        """
        解决 1146, u"Table '(.*?)' doesn't exist"
        Args:
            err_msg: 报错内容
            table_prefix: 数据表前缀
            table_enum: 数据表的枚举信息

        Returns:
            1). table_name: 数据表名
            2). table_notes: 数据表注释
            3). demand_code: 数据表对应的需求 code
        """
        table_pattern = re.compile(r"Table '(.*?)' doesn't exist")
        text = re.findall(table_pattern, err_msg)
        table = text[0].split(".")[1]

        # 写入表枚举
        if table_enum:
            for _, member in table_enum.__members__.items():
                table_name = f'{table_prefix}{member.value.get("value", "")}'
                table_notes = member.value.get("notes", "")
                demand_code = member.value.get("demand_code", "")
                if table_name == table:
                    return table_name, table_notes, demand_code
        else:
            # 未定义 Tabel_Enum 则建表
            logger.info("未定义数据库表枚举 Tabel_Enum 参数，进行创表操作")
        # 1.未定义 Tabel_Enum 和 2.正则未匹配到当前的 table_name 时都以此报错 table 名为准
        return table, "", ""

    def deal_1406_error(
        self,
        err_msg: str,
        cursor: Union[Param.PymysqlCursor, Param.PymysqlDictCursor],
        database: str,
        table: str,
        note_dic: dict,
    ) -> (str, str):
        """
        解决 1406, u"Data too long for ..."
        Args:
            err_msg: 报错内容
            conn: mysql conn
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            note_dic: 当前表字段的注释

        Returns:
            1). sql: 修改字段类型的 sql
            1). possible_err: 执行此 sql 可能会报错的信息
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
            sql = f"""ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}` {change_colum_type} NULL DEFAULT NULL COMMENT "{notes}" ;"""
            return sql, f"1406: 更新 {colum} 字段类型为 {change_colum_type} 时失败"

    def deal_1265_error(
        self,
        err_msg: str,
        cursor: Union[Param.PymysqlCursor, Param.PymysqlDictCursor],
        database: str,
        table: str,
        note_dic: dict,
    ) -> (str, str):
        """
        解决 1265, u"Data truncated for column ..."
        Args:
            err_msg: 报错内容
            cursor: mysql connect cursor
            database: 数据库名
            table: 数据表名
            note_dic: 当前表字段的注释

        Returns:
            None
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
            sql = f"""ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}` {change_colum_type} NULL DEFAULT NULL COMMENT "{notes}" ;"""
            return sql, f"1265: 更新 {colum} 字段类型为 {change_colum_type} 时失败"

    @abstractmethod
    def _exec_sql(self, *args, **kwargs) -> None:
        """
        子类要实现执行 sql 的不同方法，使得可以正常适配不同的 pipelines 场景
        Args:
            *args: None
            **kwargs: None

        Returns:
            None
        """
        pass


class Synchronize(AbstractClass):
    """
    pipeline 同步执行 sql 的场景
    """

    def _exec_sql(
        self,
        conn: Param.PymysqlConnect,
        cursor: Param.PymysqlCursor,
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
    """
    pipeline twisted 异步执行 sql 的场景
    """

    def _exec_sql(
        self,
        cursor: Param.PymysqlDictCursor,
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
    cursor: Union[Param.PymysqlCursor, Param.PymysqlDictCursor],
    charset: str,
    collate: str,
    database: str,
    table: str,
    table_prefix: str,
    table_enum: Type[TableEnumTypeVar],
    note_dic: dict,
    conn: Optional[Param.PymysqlConnect] = None,
) -> None:
    abstract_class.template_method(
        err_msg,
        conn,
        cursor,
        charset,
        collate,
        database,
        table,
        table_prefix,
        table_enum,
        note_dic,
    )
