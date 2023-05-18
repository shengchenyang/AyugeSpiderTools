# Item

> 演示在使用本库场景下 `Item` 的使用方法。

本教程将引导您完成这些任务：

- 演示本库推荐的 `Item` 适配方式
- 补充适配 `add_value`, `add_xpath`, `add_css` 等方法的示例

## 实现原理

> 以下为本库中推荐的 `mysql` 和 `MongoDB` 存储时的主要 `Item` 示例：

其实，本库就是推荐把所有字段统一存入 `alldata` 字段中，其它字段用于场景补充，比如：`table` 字段用于说明要存储的表名/集合名，`item_mode` 字段用于说明存储的方式，`mongo_update_rule` 字段是 `item_mode` 为 `MongoDB` 存储场景时的去重条件(可不设置此字段)。

本库，

```python
def parse(self, response):
	# 存储到 Mysql 场景时需要的 Item 构建示例
    ArticleMysqlItem = MysqlDataItem(
        article_detail_url=DataItem(article_detail_url, "文章详情链接"),
        article_title=DataItem(article_title, "文章标题"),
        comment_count=DataItem(comment_count, "文章评论数量"),
        favor_count=DataItem(favor_count, "文章赞成数量"),
        nick_name=DataItem(nick_name, "文章作者昵称"),
        _table=TableEnum.article_list_table.value["value"],
    )
    # 存储到 MongoDB 场景时需要的 Item 构建示例
    ArticleMongoItem = MongoDataItem(
        article_detail_url=article_detail_url,
        article_title=article_title,
        comment_count=comment_count,
        favor_count=favor_count,
        nick_name=nick_name,
        _table=TableEnum.article_list_table.value["value"],
        # 这里表示以 article_detail_url 为去重规则，若存在则更新，不存在则新增
        _mongo_update_rule={"article_detail_url": article_detail_url},
    )
```

以上可知，目前可直接将需要的参数在对应 `Item` 中直接按 `key=value` 赋值即可，`key` 即为存储至库中字段，`value` 为存储内容。

当然，目前也支持动态赋值，但是我不推荐使用，直接按照上个方式即可：

```python
 def parse(self, response):
    mdi = MysqlDataItem(_table="table0")
    mdi.add_field("add_field1", "value1")
    mdi.add_field("add_field2", DataItem(key_value="value2"))
    mdi.add_field("add_field3", DataItem(key_value="value3", notes="add_field3值"))
    # _table 修改可通过以下方式，同样不推荐使用
    mdi._table = "table1"
```

另外，本库的 `item` 提供类型转换，以方便后续的各种使用场景：

```python
# 将本库 Item 转为 dict 的方法
item_dict = mdi.asdict()
# 将本库 Item 转为 scrapy Item 的方法
item = mdi.asitem()
```

## 使用示例

> 只需要在 `yield item` 时，按需提前导入 `MysqlDataItem`， `MongoDataItem`，将所有的存储字段和场景补充字段全部添加完整即可。

以本库模板中的 `basic.tmpl` 为例：

```python
#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import pandas
from DemoSpider.settings import logger
from scrapy.http.response.text import TextResponse

from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.items import DataItem, MongoDataItem, MysqlDataItem
from ayugespidertools.spiders import AyuSpider
from scrapy.http import Request

from DemoSpider.items import TableEnum

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
            'ayugespidertools.pipelines.AyuFtyMysqlPipeline': 300,
            # 激活此项则数据会存储至 MongoDB
            'ayugespidertools.pipelines.AyuFtyMongoPipeline': 301,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 随机请求头
            'ayugespidertools.middlewares.RandomRequestUaMiddleware': 400,
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

            ArticleMysqlItem = MysqlDataItem(
                article_detail_url=DataItem(article_detail_url, "文章详情链接"),
                article_title=DataItem(article_title, "文章标题"),
                comment_count=DataItem(comment_count, "文章评论数量"),
                favor_count=DataItem(favor_count, "文章赞成数量"),
                nick_name=DataItem(nick_name, "文章作者昵称"),
                _table=TableEnum.article_list_table.value["value"],
            )
            yield ArticleMysqlItem

            ArticleMongoItem = MongoDataItem(
                article_detail_url=article_detail_url,
                article_title=article_title,
                comment_count=comment_count,
                favor_count=favor_count,
                nick_name=nick_name,
                _table=TableEnum.article_list_table.value["value"],
                # 这里表示以 article_detail_url 为去重规则，若存在则更新，不存在则新增
                _mongo_update_rule={"article_detail_url": article_detail_url},
            )
            yield ArticleMongoItem
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

| item 字段              | 类型                      | 注释                                                         |
| ---------------------- | ------------------------- | ------------------------------------------------------------ |
| **自定义字段**         | DataItem，Any             | `item` 所有需要存储的字段，若有多个，请按规则自定义添加即可。 |
| **_table**             | str                       | 存储至数据表或集合的名称                                     |
| **_item_mode**         | str("Mysql" 或 "MongoDB") | 存储类型场景，不用设置此值，有默认参数。而且赋值错误时 IDE 也会提示。 |
| **_mongo_update-rule** | dict                      | `MongoDB item` 场景下的查重规则                              |

注，对以上表格中内容进行扩充解释：

- 自定义字段使用示例请在 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/intro/tutorial.html) 中查看。

## 自定义 Item 字段和实现 Item Loaders

具体请在下一章浏览。
