#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  SqlFormat.py
@Time    :  2022/7/13 11:31
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  sql 相关处理: sql 语句的管理方法，
            这里的 sql 拼接只能做到最简单的逻辑，若想做到适配性更高，请参考 directsql, python-sql, pypika
            或 pymilk 等第三方类似功能库的实现方法，以后会再优化此场景
"""
from typing import Optional, Union


__all__ = [
    "AboutSql",
]


class AboutSql(object):
    """
    这里是生成常用的简单的 sql 语句，如果需要灵活或稍复杂的情况时，请赶快使用 pypika 等成熟的库去！
    """

    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: dict,
        base: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[Union[bool, int]] = False
    ) -> (str, tuple):
        """
        根据一些参数来生成供 pymysql 之类的库中使用的 sql 查询语句（适用于简单情况）
        Args:
            db_table: 需要查询的表名称
            key: 需要查询的关键字段
            rule: 查询需要的规则
            base: 在有多个查询规则时，选择 "and" 或 "or"，默认 "and"
            order_by: 排序的 key 值
            limit: limit 限制，默认无限制（查询所有）；如果需要则指定 int 值即可

        Returns:
            select_sql: 生成的 sql 语句
            tuple(rule.values()): 查询字段的参数名称
        """
        select_key = ", ".join(f'`{k}`' for k in key)
        select_key = select_key.replace("""`count(*)`""", "count(*)")
        # select_key = select_key.replace("""`count(1)`""", "count(1)")

        base_list = {
            "and": " and ",
            "or": " or ",
        }

        base_where = base_list[base] if base else " and "
        select_where = base_where.join(
            f"`{k.split('|')[0]}`{k.split('|')[1]}%s" for k in rule
        )
        if not order_by:
            if limit:
                select_sql = """select %s from `%s` where %s limit %s""" % (select_key, db_table, select_where, limit)
            else:
                select_sql = """select %s from `%s` where %s""" % (select_key, db_table, select_where)
        else:
            select_sql = """select %s from `%s` where %s order by %s desc limit 1""" % (
            select_key, db_table, select_where, order_by)
        """order by id desc"""
        return select_sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> (str, tuple):
        """
        根据一些参数来生成供 pymysql 之类的库中使用的 sql 插入语句
        Args:
            db_table: 需要插入的表名称
            data: 需要插入的关键字段，key: 数据表字段；value: 需插入的参数名

        Returns:
            select_sql: 生成的 sql 语句
            tuple(rule.values()): 新增字段的参数名称
        """
        keys = ", ".join(f'`{k}`' for k in data)
        values = ', '.join(['%s'] * len(data))
        sql = f'''insert into `{db_table}` ({keys}) values ({values})'''
        return sql, tuple(data.values())

    @staticmethod
    def update_generate(db_table: str, data: dict, rule: dict, base: Optional[str] = None) -> (str, tuple):
        """
        根据一些参数来生成供 pymysql 之类的库中使用的 sql 更新语句
        Args:
            db_table: 需要插入的表名称
            data: 需要更新的 key 和 value 值
            rule: 更新需要的规则
            base: 在有多个查询规则时，选择 "and" 或 "or"，默认 "and"

        Returns:
            select_sql: 生成的 sql 语句
            tuple(rule.values()): 更新字段的参数名称
        """
        update_set = ", ".join(f'`{k}`=%s' for k in data)
        base_list = {
            "and": " and ",
            "or": " or ",
        }

        base_where = base_list[base] if base else " and "
        update_where = base_where.join(f'`{k}`=%s' for k in rule)
        sql = f"""update `{db_table}` set {update_set} where {update_where}"""
        return sql, tuple(data.values()) + tuple(rule.values())
