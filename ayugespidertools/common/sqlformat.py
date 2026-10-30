from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Protocol

from ayugespidertools.common.typevars import _SENTINEL, sentinel

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
        limit: int | None = None,
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
        key: list[str],
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: int | None = None,
    ) -> tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 查询语句

        Args:
            db_table: 需要查询的表名称
            key: 需要查询的关键字段
            rule: 查询需要的规则
            base: 多查询条件
            order_by: 排序列名，不含 ASC/DESC，默认升序
            limit: limit

        Returns:
            1). sql: 生成的 sql 语句
            2). 查询字段的参数名称
        """
        select_key = ", ".join(f"`{k}`" for k in key)

        _base = f" {base} "
        select_where = _base.join(f"`{k}`=%s" for k in rule)

        sql = f"select {select_key} from `{db_table}`"
        if select_where:
            sql += f" where {select_where}"
        if order_by:
            sql += f" order by `{order_by}`"
        if limit:
            sql += f" limit {limit}"
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
        key: list[str],
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: int | None = None,
    ) -> tuple[str, tuple]:
        select_key = ", ".join(f'"{k}"' for k in key)
        _base = f" {base} "
        select_where = _base.join(f'"{k}"=%s' for k in rule)
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"select {select_key} from {db_table}"
        if select_where:
            sql += f" where {select_where}"
        if order_by:
            sql += f' order by "{order_by}"'
        if limit:
            sql += f" limit {limit}"
        return sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> tuple[str, tuple]:
        keys = ", ".join(f'"{k}"' for k in data)
        values = ", ".join(["%s"] * len(data))
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"insert into {db_table} ({keys}) values ({values})"
        return sql, tuple(data.values())

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]:
        update_set = ", ".join(f'"{k}"=%s' for k in data)

        _base = f" {base} "
        update_where = _base.join(f'"{k}"=%s' for k in rule)
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"update {db_table} set {update_set} where {update_where}"
        return sql, tuple(data.values()) + tuple(rule.values())

    @staticmethod
    def upsert_generate(
        db_table: str,
        conflict_cols: set[str],
        data: dict,
        update_cols: set[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = data.keys()
        placeholders = ", ".join(["%s"] * len(keys))
        insert_cols = ", ".join(f'"{col}"' for col in keys)
        conflict_keys = ", ".join(f'"{col}"' for col in conflict_cols)
        if update_cols:
            update_set = ", ".join(
                [f'"{col}" = EXCLUDED."{col}"' for col in update_cols]
            )
            conflict_sql = f"ON CONFLICT ({conflict_keys}) DO UPDATE SET {update_set}"
        else:
            conflict_sql = f"ON CONFLICT ({conflict_keys}) DO NOTHING"

        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"INSERT INTO {db_table} ({insert_cols}) VALUES ({placeholders}) {conflict_sql};"
        return sql, tuple(data.values())

    @staticmethod
    def merge_generate(
        db_table: str,
        match_cols: Iterable[str] | None,
        data: dict,
        update_cols: Iterable[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = data.keys()
        insert_cols = ", ".join(f'"{col}"' for col in keys)
        placeholders = ", ".join(["%s"] * len(keys))
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        if not match_cols:
            sql = f"INSERT INTO {db_table} ({insert_cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
            return sql, tuple(data.values())

        using_sql = f"(VALUES ({placeholders})) AS s({insert_cols})"
        on_sql = " AND ".join([f't."{col}" = s."{col}"' for col in match_cols])
        if not update_cols:
            when_matched_sql = ""
        else:
            update_set = ", ".join([f'"{col}" = s."{col}"' for col in update_cols])
            when_matched_sql = f"WHEN MATCHED THEN UPDATE SET {update_set}"

        insert_vals = ", ".join([f's."{col}"' for col in keys])
        sql = f"""
        MERGE INTO {db_table} AS t
        USING {using_sql}
        ON {on_sql}
        {when_matched_sql}
        WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
        """
        return sql.strip(), tuple(data.values())


class GenPostgresqlAsyncpg:
    @staticmethod
    def select_generate(
        db_table: str,
        key: list[str],
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: int | None = None,
    ) -> tuple[str, Any]:
        select_key = ", ".join(f'"{k}"' for k in key)
        _base = f" {base} "
        select_where = _base.join(f'"{k}"=${i + 1}' for i, k in enumerate(rule))
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"SELECT {select_key} FROM {db_table}"
        if select_where:
            sql += f" WHERE {select_where}"
        if order_by:
            sql += f' ORDER BY "{order_by}"'
        if limit:
            sql += f" LIMIT {limit}"
        return sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> tuple[str, Any]:
        keys = ", ".join(f'"{k}"' for k in data)
        placeholders = ", ".join(f"${i + 1}" for i, _ in enumerate(data))
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"INSERT INTO {db_table} ({keys}) VALUES ({placeholders})"
        return sql, tuple(data.values())

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: dict[str, Any], base: SqlModeStr = "and"
    ) -> tuple[str, tuple]:
        update_set = ", ".join(f'"{k}"=${i + 1}' for i, k in enumerate(data))
        offset = len(data)
        _base = f" {base} "
        update_where = _base.join(
            f'"{k}"=${i + 1 + offset}' for i, k in enumerate(rule)
        )
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"UPDATE {db_table} SET {update_set} WHERE {update_where}"
        return sql, tuple(data.values()) + tuple(rule.values())

    @staticmethod
    def upsert_generate(
        db_table: str,
        conflict_cols: set[str],
        data: dict,
        update_cols: set[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = data.keys()
        placeholders = ", ".join(f"${i + 1}" for i in range(len(keys)))
        insert_cols = ", ".join(f'"{col}"' for col in keys)
        conflict_keys = ", ".join(f'"{col}"' for col in conflict_cols)
        if update_cols:
            update_set = ", ".join(
                [f'"{col}" = EXCLUDED."{col}"' for col in update_cols]
            )
            conflict_sql = f"ON CONFLICT ({conflict_keys}) DO UPDATE SET {update_set}"
        else:
            conflict_sql = f"ON CONFLICT ({conflict_keys}) DO NOTHING"

        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        sql = f"INSERT INTO {db_table} ({insert_cols}) VALUES ({placeholders}) {conflict_sql};"
        return sql, tuple(data.values())

    @staticmethod
    def merge_generate(
        db_table: str,
        match_cols: Iterable[str] | None,
        data: dict,
        update_cols: Iterable[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = data.keys()
        insert_cols = ", ".join(f'"{col}"' for col in keys)
        placeholders = ", ".join(f"${i + 1}" for i in range(len(keys)))
        db_table = ".".join(f'"{part}"' for part in db_table.split("."))
        if not match_cols:
            sql = f"INSERT INTO {db_table} ({insert_cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
            return sql, tuple(data.values())

        using_sql = f"(VALUES ({placeholders})) AS s({insert_cols})"
        on_sql = " AND ".join([f't."{col}" = s."{col}"' for col in match_cols])
        if not update_cols:
            when_matched_sql = ""
        else:
            update_set = ", ".join([f'"{col}" = s."{col}"' for col in update_cols])
            when_matched_sql = f"WHEN MATCHED THEN UPDATE SET {update_set}"

        insert_vals = ", ".join([f's."{col}"' for col in keys])
        sql = f"""
        MERGE INTO {db_table} AS t
        USING {using_sql}
        ON {on_sql}
        {when_matched_sql}
        WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
        """
        return sql.strip(), tuple(data.values())


class GenOracle:
    @staticmethod
    def select_generate(
        db_table: str,
        key: list[str],
        rule: dict[str, Any],
        base: SqlModeStr = "and",
        order_by: str | None = None,
        limit: int | _SENTINEL = sentinel,
    ) -> tuple[str, tuple]:
        select_key = ", ".join(f'"{k}"' for k in key)
        _base = f" {base} "
        select_where = _base.join(f'"{k}"=:{i + 1}' for i, k in enumerate(rule))

        sql = f'select {select_key} from "{db_table}"'
        if select_where:
            sql += f" where {select_where}"
        if order_by:
            sql += f' order by "{order_by}"'
        if limit is not sentinel:
            sql = f"select * from ({sql}) where ROWNUM <= {limit}"
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
    def merge_generate(
        db_table: str,
        match_cols: Iterable[str] | None,
        data: dict[str, Any],
        update_cols: Iterable[str] | None = None,
    ) -> tuple[str, tuple]:
        keys = data.keys()
        insert_cols = ", ".join([f'"{col}"' for col in keys])
        if not match_cols:
            placeholders = ", ".join(f":{i + 1}" for i in range(len(keys)))
            sql = f'INSERT INTO "{db_table}" ({insert_cols}) VALUES ({placeholders})'
            return sql.strip(), tuple(data.values())

        select_part = ", ".join(f':{i + 1} "{col}"' for i, col in enumerate(keys))
        using_sql = f"(SELECT {select_part} FROM dual) s"
        on_sql = " AND ".join([f't."{col}" = s."{col}"' for col in match_cols])
        if not update_cols:
            when_matched_sql = ""
        else:
            update_set = ", ".join([f't."{col}" = s."{col}"' for col in update_cols])
            when_matched_sql = f"WHEN MATCHED THEN UPDATE SET {update_set}"
        insert_vals = ", ".join([f's."{col}"' for col in keys])
        sql = f"""
        MERGE INTO "{db_table}" t
        USING {using_sql}
        ON ({on_sql})
        {when_matched_sql}
        WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
        """
        return sql.strip(), tuple(data.values())
