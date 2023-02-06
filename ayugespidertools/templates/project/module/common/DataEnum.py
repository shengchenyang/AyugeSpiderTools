from enum import Enum, unique


@unique
class TableEnum(Enum):
    """
    数据库表枚举信息示例，用于限制存储信息类的字段及值不允许重复和修改
    """

    article_list_table = {
        "value": "article_info_list",
        "notes": "项目列表信息",
        "demand_code": "DemoSpider_article_list_table_demand_code",
    }
