from __future__ import annotations

from typing import Any, Literal, Protocol

__all__ = [
    "GenMysql",
    "GenPostgresql",
    "GenPostgresqlAsyncpg",
    "GenOracle",
]

SqlModeStr = Literal["and", "or"]


class GenSql(Protocol):
    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: bool | int = False,
        vertical: bool = True,
    ): ...

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> tuple[str, tuple]: ...

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]: ...


class GenMysql:
    """mysql 语句的生成方法，只适用简单场景。"""

    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: bool | int = False,
        vertical: bool = True,
    ) -> tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 查询语句

        Args:
            db_table: 需要查询的表名称
            key: 需要查询的关键字段
            rule: 查询需要的规则
            base: 多查询条件
            order_by: 排序的 key 值
            limit: limit
            vertical: rule 的规则是否是 | 分隔

        Returns:
            1). sql: 生成的 sql 语句
            2). 查询字段的参数名称
        """
        select_key = ", ".join(k if k in {1, "1"} else f"`{k}`" for k in key)
        select_key = select_key.replace("""`count(*)`""", "count(*)")
        select_key = select_key.replace("""`count(1)`""", "count(1)")

        _base = f" {base} "
        if vertical:
            select_where = _base.join(
                f"`{k.split('|')[0]}`{k.split('|')[1]}%s" for k in rule
            )
        else:
            select_where = _base.join(f"`{k}`=%s" for k in rule)

        _where = f"where {select_where}" if select_where else ""
        _order_by = f"order by {order_by}" if order_by else ""
        _limit = f"limit {limit}" if limit else ""
        sql = f"""select {select_key} from {db_table} {_where} {_order_by} {_limit}"""
        return sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 插入语句

        Args:
            db_table: 需要插入的表名称
            data: 需要插入的关键字段，key: 数据表字段；value: 需插入的参数名

        Returns:
            1). sql: 生成的 sql 语句
            2). 新增字段的参数名称
        """
        keys = ", ".join(f"`{k}`" for k in data)
        values = ", ".join(["%s"] * len(data))
        sql = f"""insert into `{db_table}` ({keys}) values ({values})"""
        return sql, tuple(data.values())

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 更新语句

        Args:
            db_table: 需要插入的表名称
            data: 需要更新的 key 和 value 值
            rule: 更新需要的规则
            base: 多查询条件

        Returns:
            1). sql: 生成的 sql 语句
            2). 更新字段的参数名称
        """
        update_set = ", ".join(f"`{k}`=%s" for k in data)

        _base = f" {base} "
        update_where = _base.join(f"`{k}`=%s" for k in rule)
        sql = f"""update `{db_table}` set {update_set} where {update_where}"""
        return sql, tuple(data.values()) + tuple(rule.values())


class GenPostgresql:
    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: bool | int = False,
        vertical: bool = True,
    ) -> tuple[str, tuple]:
        select_key = ", ".join(k if k in {1, "1"} else f"{k}" for k in key)
        select_key = select_key.replace('''"count(*)"''', "count(*)")
        select_key = select_key.replace('''"count(1)"''', "count(1)")

        _base = f" {base} "
        if vertical:
            select_where = _base.join(
                f'{k.split("|")[0]}{k.split("|")[1]}%s' for k in rule
            )
        else:
            select_where = _base.join(f"{k}=%s" for k in rule)

        _where = f"where {select_where}" if select_where else ""
        _order_by = f"order by {order_by}" if order_by else ""
        _limit = f"limit {limit}" if limit else ""
        sql = f"""select {select_key} from {db_table} {_where} {_order_by} {_limit}"""
        return sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> tuple[str, tuple]:
        keys = ", ".join(f"{k}" for k in data)
        values = ", ".join(["%s"] * len(data))
        sql = f"""insert into {db_table} ({keys}) values ({values})"""
        return sql, tuple(data.values())

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]:
        update_set = ", ".join(f"{k}=%s" for k in data)

        _base = f" {base} "
        update_where = _base.join(f"{k}=%s" for k in rule)
        sql = f"""update {db_table} set {update_set} where {update_where}"""
        return sql, tuple(data.values()) + tuple(rule.values())


class GenPostgresqlAsyncpg:
    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: bool | int = False,
        vertical: bool = True,
    ) -> tuple[str, Any]:
        select_key = ", ".join(k if k in {1, "1"} else f"{k}" for k in key)
        select_key = select_key.replace('''"count(*)"''', "count(*)")
        select_key = select_key.replace('''"count(1)"''', "count(1)")

        _base = f" {base} "
        if vertical:
            select_where = _base.join(
                f"{k.split('|')[0]}{k.split('|')[1]}${i + 1}"
                for i, k in enumerate(rule)
            )
        else:
            select_where = _base.join(f"{k}=${i + 1}" for i, k in enumerate(rule))

        _where = f"WHERE {select_where}" if select_where else ""
        _order_by = f"ORDER BY {order_by}" if order_by else ""
        _limit = f"LIMIT {limit}" if limit else ""

        sql = f"SELECT {select_key} FROM {db_table} {_where} {_order_by} {_limit}"
        return sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> tuple[str, Any]:
        keys = ", ".join(data.keys())
        placeholders = ", ".join(f"${i + 1}" for i, _ in enumerate(data))
        sql = f"INSERT INTO {db_table} ({keys}) VALUES ({placeholders})"
        return sql, data.values()

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]:
        update_set = ", ".join(f"{k}=${i + 1}" for i, k in enumerate(data))
        offset = len(data)
        _base = f" {base} "
        update_where = _base.join(f"{k}=${i + 1 + offset}" for i, k in enumerate(rule))
        sql = f"UPDATE {db_table} SET {update_set} WHERE {update_where}"
        return sql, tuple(data.values()) + tuple(rule.values())


class GenOracle:
    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: bool | int = False,
        vertical: bool = True,
    ) -> tuple[str, tuple]:
        select_key = ", ".join(k if k in {1, "1"} else f"`{k}`" for k in key)
        select_key = select_key.replace("""`count(*)`""", "count(*)")
        select_key = select_key.replace("""`count(1)`""", "count(1)")

        _base = f" {base} "
        if vertical:
            select_where = _base.join(
                f"""'"{k.split("|")[0]}"{k.split("|")[1]}:{i + 1}"""
                for i, k in enumerate(rule)
            )
        else:
            select_where = _base.join(f'"{k}"=:{i + 1}' for i, k in enumerate(rule))

        _where = f"where {select_where}" if select_where else ""
        _order_by = f"order by {order_by}" if order_by else ""
        _limit = f"limit {limit}" if limit else ""
        _limit = f"AND ROWNUM = {limit}" if limit else ""
        sql = f"""select {select_key} from "{db_table}" {_where} {_order_by} {_limit}"""
        return sql, tuple(rule.values())

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]:
        update_set = ", ".join(f'"{k}"=:{i + 1}' for i, k in enumerate(data))

        _base = f" {base} "
        update_where = _base.join(
            f'"{k}"=:{i + 1 + len(data)}' for i, k in enumerate(rule)
        )
        sql = f"""update "{db_table}" set {update_set} where {update_where}"""
        return sql, tuple(data.values()) + tuple(rule.values())
