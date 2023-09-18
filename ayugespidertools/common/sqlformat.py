from typing import Any, Dict, Literal, Optional, Tuple, Union

__all__ = [
    "AboutSql",
]

SqlModeStr = Literal["and", "or"]


class AboutSql:
    """sql 相关处理: sql 语句的管理方法，
    这里的 sql 拼接只能做到最简单的逻辑，如果需要灵活或稍复杂的情况，请参考 directsql, python-sql, pypika
    或 pymilk 等第三方类似功能库的实现方法，以后会再优化此场景
    """

    @staticmethod
    def select_generate(
        db_table: str,
        key: list,
        rule: Dict[str, Any],
        base: SqlModeStr = "and",
        order_by: Optional[str] = None,
        limit: Union[bool, int] = False,
    ) -> Tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 查询语句（适用于简单情况）

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
        select_key = ", ".join(f"`{k}`" for k in key)
        select_key = select_key.replace("""`count(*)`""", "count(*)")
        select_key = select_key.replace("""`count(1)`""", "count(1)")

        _base = f" {base} "
        select_where = _base.join(
            f"`{k.split('|')[0]}`{k.split('|')[1]}%s" for k in rule
        )

        _where = f"where {select_where}" if select_where else ""
        _order_by = f"order by {order_by}" if order_by else ""
        _limit = f"limit {limit}" if limit else ""
        select_sql = (
            f"""select {select_key} from {db_table} {_where} {_order_by} {_limit}"""
        )
        return select_sql, tuple(rule.values())

    @staticmethod
    def insert_generate(db_table: str, data: dict) -> Tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 插入语句

        Args:
            db_table: 需要插入的表名称
            data: 需要插入的关键字段，key: 数据表字段；value: 需插入的参数名

        Returns:
            select_sql: 生成的 sql 语句
            tuple(rule.values()): 新增字段的参数名称
        """
        keys = ", ".join(f"`{k}`" for k in data)
        values = ", ".join(["%s"] * len(data))
        sql = f"""insert into `{db_table}` ({keys}) values ({values})"""
        return sql, tuple(data.values())

    @staticmethod
    def update_generate(
        db_table: str, data: dict, rule: Dict[str, Any], base: SqlModeStr = "and"
    ) -> Tuple[str, tuple]:
        """根据一些参数来生成供 pymysql 之类的库中使用的 sql 更新语句

        Args:
            db_table: 需要插入的表名称
            data: 需要更新的 key 和 value 值
            rule: 更新需要的规则
            base: 在有多个查询规则时，选择 "and" 或 "or"，默认 "and"

        Returns:
            select_sql: 生成的 sql 语句
            tuple(rule.values()): 更新字段的参数名称
        """
        update_set = ", ".join(f"`{k}`=%s" for k in data)

        _base = f" {base} "
        update_where = _base.join(f"`{k}`=%s" for k in rule)
        sql = f"""update `{db_table}` set {update_set} where {update_where}"""
        return sql, tuple(data.values()) + tuple(rule.values())
