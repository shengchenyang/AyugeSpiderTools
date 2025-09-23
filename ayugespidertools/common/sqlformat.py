from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Protocol

__all__ = [
    "GenMysql",
    "GenOracle",
    "GenPostgresql",
    "GenPostgresqlAsyncpg",
]

if TYPE_CHECKING:
    from collections.abc import Iterable

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
                f"{k.split('|')[0]}{k.split('|')[1]}%s" for k in rule
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

    @staticmethod
    def upsert_generate(
        db_table: str,
        conflict_cols: set[str],
        data: dict,
        update_cols: set[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = list(data.keys())
        placeholders = ", ".join(["%s"] * len(keys))
        insert_cols = ", ".join(keys)
        if update_cols:
            update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])
            conflict_sql = (
                f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET {update_set}"
            )
        else:
            conflict_sql = f"ON CONFLICT ({', '.join(conflict_cols)}) DO NOTHING"

        sql = f"INSERT INTO {db_table} ({insert_cols}) VALUES ({placeholders}) {conflict_sql};"
        return sql, tuple(data.values())


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

    @staticmethod
    def upsert_generate(
        db_table: str,
        conflict_cols: set[str],
        data: dict,
        update_cols: set[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = list(data.keys())
        placeholders = ", ".join(f"${i + 1}" for i in range(len(keys)))
        insert_cols = ", ".join(keys)
        if update_cols:
            update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])
            conflict_sql = (
                f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET {update_set}"
            )
        else:
            conflict_sql = f"ON CONFLICT ({', '.join(conflict_cols)}) DO NOTHING"

        sql = f"INSERT INTO {db_table} ({insert_cols}) VALUES ({placeholders}) {conflict_sql};"
        return sql, tuple(data.values())

    @staticmethod
    def merge_generate(
        db_table: str,
        match_cols: list[str],
        data: dict,
        update_cols: list[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = list(data.keys())
        placeholders = ", ".join(f"${i + 1}" for i in range(len(keys)))
        using_sql = f"(VALUES ({placeholders})) AS s({', '.join(keys)})"
        on_sql = " AND ".join([f"t.{col} = s.{col}" for col in match_cols])
        if update_cols is None:
            update_cols = [k for k in keys if k not in match_cols]
        update_set = ", ".join([f"{col} = s.{col}" for col in update_cols])

        insert_cols = ", ".join(keys)
        insert_vals = ", ".join([f"s.{col}" for col in keys])
        sql = f"""
        MERGE INTO {db_table} AS t
        USING {using_sql}
        ON {on_sql}
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols}) VALUES ({insert_vals})
        """
        return sql.strip(), tuple(data.values())


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

    @staticmethod
    def upsert_generate(
        db_table: str,
        conflict_cols: set[str],
        data: dict[str, Any],
        update_cols: Iterable[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = list(data.keys())
        placeholders = ", ".join(f":{i + 1}" for i in range(len(keys)))
        insert_cols = ", ".join([f'"{col}"' for col in keys])
        if update_cols:
            update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])
            conflict_sql = (
                f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET {update_set}"
            )
        else:
            conflict_sql = f"ON CONFLICT ({', '.join(conflict_cols)}) DO NOTHING"

        sql = f'INSERT INTO "{db_table}" ({insert_cols}) VALUES ({placeholders}) {conflict_sql}'
        return sql, tuple(data.values())

    @staticmethod
    def merge_generate(
        db_table: str,
        match_cols: Iterable[str] | None,
        data: dict[str, Any],
        update_cols: Iterable[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = list(data.keys())
        insert_cols = ", ".join([f'"{col}"' for col in keys])
        if not match_cols:
            placeholders = ", ".join(f":{i + 1}" for i in range(len(keys)))
            sql = f'INSERT INTO "{db_table}" ({insert_cols}) VALUES ({placeholders})'
            return sql.strip(), tuple(data.values())

        select_part = ", ".join(f':{i + 1} "{col}"' for i, col in enumerate(keys))
        using_sql = f"(SELECT {select_part} FROM dual) s"
        on_sql = " AND ".join([f't."{col}" = s."{col}"' for col in match_cols])
        if update_cols is None:
            update_cols = [k for k in keys if k not in match_cols]
        update_set = ", ".join([f't."{col}" = s."{col}"' for col in update_cols])
        insert_vals = ", ".join([f's."{col}"' for col in keys])
        sql = f"""
        MERGE INTO "{db_table}" t
        USING {using_sql}
        ON ({on_sql})
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_cols}) VALUES ({insert_vals})
        """
        return sql.strip(), tuple(data.values())
