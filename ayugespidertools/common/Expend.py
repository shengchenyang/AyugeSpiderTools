#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  Params.py
@Time    :  2023/1/20 16:32
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import re
import pymysql
import datetime
from retrying import retry
from typing import Optional
from ayugespidertools.config import logger
from ayugespidertools.common.Params import Param
from ayugespidertools.common.MultiPlexing import ReuseOperation


__all__ = [
    'MysqlErrorHandlingMixin',
]


class MysqlErrorHandlingMixin(object):
    """
    用于解决 pipelines 中数据库常遇的错误，作为 Mixin 使用，不要对其实例化和单独使用等
    """

    def get_column_type(
        self,
        conn,
        cursor,
        database: str,
        table: str,
        column: str
    ) -> str:
        """
        获取数据字段存储类型
        Args:
            conn: mysql 连接
            cursor: mysql 句柄
            database: 数据库
            table: 数据表
            column: 字段名称

        Returns:
            column_type: 字段存储类型
        """
        sql = f'''select COLUMN_TYPE from information_schema.columns where table_schema = '{database}' and 
            table_name = '{table}' and COLUMN_NAME= '{column}';'''
        column_type = None
        try:
            if conn:
                conn.ping(reconnect=True)

            if res := cursor.execute(sql):
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

    def create_table(
        self,
        cursor,
        table_name: str,
        charset: str,
        collate: str,
        tabel_notes: Optional[str] = "",
        demand_code: Optional[str] = ""
    ) -> None:
        """
        创建数据库表
        Args:
            cursor: cursor
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

        sql = f'''CREATE TABLE `{table_name}` (`id` int(32) NOT NULL AUTO_INCREMENT COMMENT 'id',
            PRIMARY KEY (`id`)) ENGINE=InnoDB DEFAULT CHARSET={charset} 
            COLLATE={collate} COMMENT='{tabel_notes}'; '''
        try:
            # 执行 sql 查询，获取数据
            data = cursor.execute(sql)
            if any([data == 0, not data]):
                logger.info(f"创建数据表 {tabel_notes}: {table_name} 成功！")

        except Exception as e:
            logger.error(f"创建表失败，tabel_notes：{tabel_notes}，table_name：{table_name}，error：{e}")

    @retry(stop_max_attempt_number=Param.retry_num, wait_random_min=Param.retry_time_min,
           wait_random_max=Param.retry_time_max)
    def _connect(self, pymysql_dict_config):
        try:
            conn = pymysql.connect(**pymysql_dict_config)
        except Exception as e:
            logger.warning(f"目标数据库：{pymysql_dict_config['database']} 不存在，尝试创建中...")
            if "1049" in str(e):
                # 如果连接目标数据库报不存在的错误时，先创建出此目标数据库
                ReuseOperation.create_database(pymysql_dict_config)
        else:
            # 连接没有问题就直接返回连接对象
            return conn
        # 出现数据库不存在问题后，在创建数据库 create_database 后，再次返回连接对象
        return pymysql.connect(**pymysql_dict_config)

    def deal_1054_error(self, err_msg: str, conn, cursor, table: str, note_dic: dict):
        """
        解决 1054, u"Unknown column 'id' in 'field list'"
        Args:
            err_msg: 报错内容
            conn: mysql 连接
            cursor: mysql 连接句柄
            table: 表名
            note_dic: 当前表字段的注释

        Returns:
            None
        """
        colum_pattern = re.compile(r"Unknown column '(.*?)' in 'field list'")
        text = re.findall(colum_pattern, err_msg)
        colum = text[0]
        notes = note_dic[colum]

        if colum == "url":
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` TEXT(500) NULL COMMENT '{notes}';"
        elif colum in ["create_time", "crawl_time"]:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` DATE NULL DEFAULT NULL COMMENT '{notes}';"
        else:
            sql = f"ALTER TABLE `{table}` ADD COLUMN `{colum}` VARCHAR(190) NULL DEFAULT '' COMMENT '{notes}';"

        try:
            if conn:
                conn.ping(reconnect=True)
                if cursor.execute(sql):
                    conn.commit()
            else:
                cursor.execute(sql)
        except Exception as e:
            if "1060" in str(e):
                logger.info(f"添加字段 {colum} 已存在")
            else:
                logger.info(f"{e}")

    def deal_1146_error(self, err_msg: str, table_prefix, cursor, charset, collate, table_enum):
        table_pattern = re.compile(r"Table '(.*?)' doesn't exist")
        text = re.findall(table_pattern, err_msg)
        table = text[0].split(".")[1]

        # 写入表枚举
        have_create_flag = False
        if table_enum:
            for name, member in table_enum.__members__.items():
                table_name = f'{table_prefix}{member.value.get("value", "")}'
                table_notes = member.value.get("notes", "")
                demand_code = member.value.get("demand_code", "")
                if table_name == table:
                    have_create_flag = True
                    self.create_table(
                        cursor=cursor,
                        table_name=table_name,
                        charset=charset,
                        collate=collate,
                        tabel_notes=table_notes,
                        demand_code=demand_code
                    )
                    break
            if have_create_flag is False:
                self.create_table(
                    cursor=cursor,
                    table_name=table,
                    charset=charset,
                    collate=collate,
                    tabel_notes="",
                    demand_code=""
                )

        else:
            # 未定义 Tabel_Enum 则建表
            logger.info("未定义数据库表枚举 Tabel_Enum 参数，进行创表操作")
            self.create_table(
                cursor=cursor,
                table_name=table,
                charset=charset,
                collate=collate,
                tabel_notes="",
                demand_code=""
            )

    def deal_1406_error(self, err_msg: str, conn, cursor, database: str, table: str, note_dic: dict):
        if "Data too long for" in err_msg:
            colum_pattern = re.compile(r"Data too long for column '(.*?)' at")
            text = re.findall(colum_pattern, err_msg)
            colum = text[0]
            notes = note_dic[colum]
            column_type = self.get_column_type(conn=conn, cursor=cursor, database=database, table=table, column=colum)
            change_colum_type = "LONGTEXT" if column_type == "text" else "TEXT"
            sql = f"""ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}` {change_colum_type} NULL DEFAULT NULL COMMENT "{notes}" ;"""

            try:
                if conn:
                    conn.ping(reconnect=True)
                    if cursor.execute(sql):
                        conn.commit()
                else:
                    cursor.execute(sql)
            except Exception as e:
                logger.error(f"更新字段类型失败 {e}")
        else:
            logger.error(f"1406 的其它错误类型: {err_msg}")
            raise Exception(f"1406 的其它错误类型: {err_msg}")

    def deal_1265_error(self, err_msg: str, conn, cursor, database: str, table: str, note_dic: dict):
        if "Data truncated for column" in err_msg:
            colum_pattern = re.compile(r"Data truncated for column '(.*?)' at")
            text = re.findall(colum_pattern, err_msg)
            colum = text[0]
            notes = note_dic[colum]
            column_type = self.get_column_type(conn=conn, cursor=cursor, database=database, table=table, column=colum)
            change_colum_type = "LONGTEXT" if column_type == "text" else "TEXT"
            sql = f"""ALTER TABLE `{table}` CHANGE COLUMN `{colum}` `{colum}` {change_colum_type} NULL DEFAULT NULL COMMENT "{notes}" ;"""
            try:
                if conn:
                    conn.ping(reconnect=True)
                    if cursor.execute(sql):
                        conn.commit()
                else:
                    cursor.execute(sql)
            except Exception as e:
                logger.error(f"更新字段类型失败 {e}")
        else:
            logger.error(f"1265 的其它错误类型: {err_msg}")
            raise Exception(f"1265 的其它错误类型: {err_msg}")

    def _get_log_by_spider(self, spider, crawl_time):
        mysql_config = spider.mysql_config
        text = {}
        stats = spider.stats.get_stats()
        error_reason = ""
        for k, v in stats.items():
            if isinstance(v, datetime.datetime):
                text[k.replace("/", "_")] = (v + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                if all(["response_status_count" in k, k != "downloader/response_status_count/200"]):
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
            "database": mysql_config["database"],
            # 脚本名称
            "spider_name": spider.name,
            # uid
            "uid": f'{mysql_config["database"]}|{spider.name}',
            # 请求次数统计
            "request_counts": text.get("downloader_request_count", 0),
            # 接收次数统计
            "received_count": text.get("response_received_count", 0),
            # 采集数据量
            "item_counts": text.get("item_scraped_count", 0),
            # info 数据统计
            "info_count": text.get("log_count_INFO", 0),
            # 警告数据统计
            "warning_count": text.get("log_count_WARNING", 0),
            # 错误数据统计
            "error_count": text.get("log_count_ERROR", 0),
            # 开始时间
            "start_time": text.get("start_time"),
            # 结束时间
            "finish_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            # 花费时间
            "spend_minutes": round(
                (datetime.datetime.now() - stats.get("start_time") - datetime.timedelta(hours=8)).seconds / 60, 2),
            "crawl_time": crawl_time
        }

        # 错误原因
        if text.get("log_count_ERROR", 0):
            log_info["log_count_ERROR"] = error_reason or "请人工排查错误原因！"

        else:
            log_info["log_count_ERROR"] = ""
        return log_info
