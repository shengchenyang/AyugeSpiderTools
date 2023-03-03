# Item

> 演示在使用本库场景下 `Item` 的使用方法。

本教程将引导您完成这些任务：

- 演示本库推荐的 `Item` 适配方式
- 补充适配 `add_value`, `add_xpath`, `add_css` 等方法的示例

## 实现原理

> 以下为本库中推荐的 `mysql` 和 `MongoDB` 存储时的主要 `Item` 示例：

其实，本库就是推荐把所有字段统一存入 `alldata` 字段中，其它字段用于场景补充，比如：`table` 字段用于说明要存储的表名/集合名，`item_mode` 字段用于说明存储的方式，`mongo_update_rule` 字段是 `item_mode` 为 `MongoDB` 存储场景时的去重条件(可不设置此字段)。

```python
@dataclass
class BaseItem:
    """
    用于构建 scrapy item 的基本结构，所有需要存储的表对应的结构都放在 alldata 中
    """
    alldata: dict = field(default=None)
    table: str = field(default=None)


@dataclass
class MysqlDataItem(BaseItem):
    """
    这个是 Scrapy item 的 Mysql 的存储结构
    """
    item_mode: str = field(default="Mysql")


@dataclass
class MongoDataItem(BaseItem):
    """
    这个是 Scrapy item 的 MongoDB 的存储结构
    这个 mongo_update_rule 字段是用于 Mongo 存储时作查询使用
    """
    item_mode: str = field(default="MongoDB")
    mongo_update_rule: dict = field(default=None)
```

## 使用示例

> 只需要在 `yield item` 时，按需提前导入 `MysqlDataItem`， `MongoDataItem`，将所有的存储字段和场景补充字段全部添加完整即可。

以本库模板中的 `basic.tmpl` 为例：

```python
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import pandas
from scrapy.http import Request
from DemoSpider.settings import logger
from scrapy.http.response.text import TextResponse
from DemoSpider.common.DataEnum import TableEnum
from ayugespidertools.AyugeSpider import AyuSpider
from ayugespidertools.common.Utils import ToolsForAyu
from ayugespidertools.Items import MysqlDataItem, MongoDataItem

"""
####################################################################################################
# collection_website: csdn.net - 采集的目标站点介绍
# collection_content: 采集内容介绍
# create_time: xxxx-xx-xx
# explain:
# demand_code_prefix = ''
####################################################################################################
"""


class DemoOneSpider(AyuSpider):
    name = 'demo_one'
    allowed_domains = ['csdn.net']
    start_urls = ['https://www.csdn.net/']

    # 数据库表的枚举信息
    custom_table_enum = TableEnum
    # 初始化配置的类型
    settings_type = 'debug'
    custom_settings = {
        # scrapy 日志等级配置
        'LOG_LEVEL': 'DEBUG',
        # 以 loguru 来管理日志，本库会在 settings 中生成规则示例，可自行修改。也可不配置
        'LOGURU_CONFIG': logger,
        # Mysql数据表的前缀名称，用于标记属于哪个项目，可不配置
        'MYSQL_TABLE_PREFIX': "demo_basic_",
        # MongoDB 集合的前缀名称，用于标记属于哪个项目，可不配置
        'MONGODB_COLLECTION_PREFIX': "demo_basic_",
        'ITEM_PIPELINES': {
            # 激活此项则数据会存储至 Mysql
            'ayugespidertools.Pipelines.AyuFtyMysqlPipeline': 300,
            # 激活此项则数据会存储至 MongoDB
            'ayugespidertools.Pipelines.AyuFtyMongoPipeline': 301,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 随机请求头
            'ayugespidertools.Middlewares.RandomRequestUaMiddleware': 400,
        },
    }

    # 打开 mysql 引擎开关，用于数据入库前更新逻辑判断
    mysql_engine_enabled = True

    def start_requests(self):
        """
        get 请求首页，获取项目列表数据
        """
        yield Request(
            url="https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=",
            callback=self.parse_first,
            headers={
                'referer': 'https://blog.csdn.net/rank/list',
            },
            cb_kwargs={
                "curr_site": "csdn",
            },
            dont_filter=True
        )

    def parse_first(self, response: TextResponse, curr_site: str):
        # 日志使用: scrapy 的 self.logger 或本库的 self.slog 或直接使用全局的 logger handle 也行（根据场景自行选择）
        self.slog.info(f"当前采集的站点为: {curr_site}")

        # 你可以自定义解析规则，使用 lxml 还是 response.css response.xpath 等等都可以。
        data_list = ToolsForAyu.extract_with_json(json_data=response.json(), query="data")
        for curr_data in data_list:
            article_detail_url = ToolsForAyu.extract_with_json(
                json_data=curr_data,
                query="articleDetailUrl")

            article_title = ToolsForAyu.extract_with_json(
                json_data=curr_data,
                query="articleTitle")

            comment_count = ToolsForAyu.extract_with_json(
                json_data=curr_data,
                query="commentCount")

            favor_count = ToolsForAyu.extract_with_json(
                json_data=curr_data,
                query="favorCount")

            nick_name = ToolsForAyu.extract_with_json(
                json_data=curr_data,
                query="nickName")

            # 这是需要存储的字段信息
            article_info = {
                "article_detail_url": {'key_value': article_detail_url, 'notes': '文章详情链接'},
                "article_title": {'key_value': article_title, 'notes': '文章标题'},
                "comment_count": {'key_value': comment_count, 'notes': '文章评论数量'},
                "favor_count": {'key_value': favor_count, 'notes': '文章赞成数量'},
                "nick_name": {'key_value': nick_name, 'notes': '文章作者昵称'}
            }

            ArticleInfoMysqlItem = MysqlDataItem(
                alldata=article_info,
                table=TableEnum.article_list_table.value['value'],
            )
            self.slog.info(f"ArticleInfoMysqlItem: {ArticleInfoMysqlItem}")

            # 数据入库逻辑，你可以使用 mysql_engine 来去重或自定义规则
            try:
                sql = '''select `id` from `{}` where `article_detail_url` = "{}" limit 1'''.format(
                    self.custom_settings.get('MYSQL_TABLE_PREFIX', '') + TableEnum.article_list_table.value['value'],
                    article_detail_url)
                df = pandas.read_sql(sql, self.mysql_engine)

                # 如果为空，说明此数据不存在于数据库，则新增
                if df.empty:
                    yield ArticleInfoMysqlItem

                # 如果已存在，1). 若需要更新，请自定义更新数据结构和更新逻辑；2). 若不用更新，则跳过即可。
                else:
                    self.slog.debug(f"标题为 ”{article_title}“ 的数据已存在")

            except Exception as e:
                if any(["1146" in str(e), "1054" in str(e), "doesn't exist" in str(e)]):
                    yield ArticleInfoMysqlItem
                else:
                    self.slog.error(f"请查看数据库链接或网络是否通畅！Error: {e}")

            # 这是 MongoDB 存储场景的示例
            ArticleInfoMongoItem = MongoDataItem(
                # alldata 用于存储 mongo 的 Document 文档所需要的字段映射
                alldata=article_info,
                # table 为 mongo 的存储 Collection 集合的名称
                table=TableEnum.article_list_table.value['value'],
                # mongo_update_rule 为查询数据是否存在的规则
                mongo_update_rule={"article_detail_url": article_detail_url},
            )
            yield ArticleInfoMongoItem
```

> 由上可知，本库中的 `Item` 使用方法还是很方便的。
>

**对以上 `Item` 相关信息解释：**

- 先导入所需 `Item`
  - `mysql` 场景导入 `MysqlDataItem`
  - `mongo` 场景导入 `MongoDataItem`
- 构建对应场景的 `Item`
  - `MysqlDataItem` 构建 `Mysql` 存储场景
  - `MongoDataItem` 构建 `MongoDB` 存储场景
- 最后 `yield` 对应 `item` 即可

## yield item

> 这里解释下 `item` 的格式问题，虽说也是支持直接 `yield dict` ，`scrapy` 的 `item` 格式(即 `ScrapyClassicItem`)，还有就是本库推荐的 `MysqlDataItem` 和 `MongoDataItem` 的形式。

这里介绍下 `item` 字段及其注释，以上所有 `item` 都有参数提示：

| item 字段             | 类型                      | 注释                                              |
| --------------------- | ------------------------- | ------------------------------------------------- |
| **alldata**           | dict(单层，或双层)        | `item` 所有需要存储的字段，其格式分类请在下方查看 |
| **table**             | str                       | 存储至数据表或集合的名称                          |
| **item_mode**         | str("Mysql" 或 "MongoDB") | 存储类型场景                                      |
| **mongo_update-rule** | dict                      | `MongoDB item` 场景下的查重规则                   |

注，对以上表格中内容进行扩充解释：

- `alldata` 字段格式：
  
  - ```python
    # alldata 示例一，推荐此代码编写风格
    alldata1 = {
        "article_detail_url": {
            "key_value": article_detail_url,
            "notes": "文章详情链接",
        },
        "article_title": {
            "key_value": article_title,
            "notes": "文章标题",
        },
    }
    ```
  
  - ```python
    # alldata 示例二
    alldata2 = {
        "article_detail_url": article_detail_url,
        "article_title": article_title,
    }
    ```

## 自定义 Item 字段和实现 Item Loaders

> 本库支持 [scrapy Item](https://docs.scrapy.org/en/latest/topics/items.html) 的格式，或者 `dict` 格式，`DemoSpider` 中 [demo_one](https://github.com/shengchenyang/DemoSpider/blob/main/DemoSpider/spiders/demo_one.py) 已有示例。

由于本库推荐将所有存储字段统一存储至 `alldata` 中来维护的，而且本库 `Item` 已使用了 `scrapy` 推荐的 [dataclass](https://docs.python.org/zh-cn/3/library/dataclasses.html) 实现，自然是不推荐自定义 `Item` 字段的，但是也是可以实现的。具体请在下一章浏览。
