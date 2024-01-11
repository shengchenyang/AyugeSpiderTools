# Item

> 演示在使用本库场景下 `Item` 的使用方法。

本教程将引导您完成这些任务：

- 演示本库推荐的 `Item` 适配方式
- 补充适配 `add_value`, `add_xpath`, `add_css` 等方法的示例

## 实现原理

> 以下为本库中推荐的 `mysql` 和 `MongoDB` 存储时的主要 `Item` 示例：

本库将所有需要存储的字段直接在对应的 `Item` (`AyuItem`) 中赋值即可，其中 `_table` 参数为必须参数，也可以使用 `add_field` 方法动态添加字段。

```python
def parse(self, response):
    # 存储到 Mysql 场景时需要的 Item 构建示例
    ArticleMysqlItem = AyuItem(
        article_detail_url=DataItem(article_detail_url, "文章详情链接"),
        article_title=DataItem(article_title, "文章标题"),
        comment_count=DataItem(comment_count, "文章评论数量"),
        favor_count=DataItem(favor_count, "文章赞成数量"),
        nick_name=DataItem(nick_name, "文章作者昵称"),
        _table=DataItem("_article_info_list", "文章信息列表"),
    )

    # 存储到 MongoDB 场景时需要的 Item 构建示例
    ArticleMongoItem = AyuItem(
        article_detail_url=article_detail_url,
        article_title=article_title,
        comment_count=comment_count,
        favor_count=favor_count,
        nick_name=nick_name,
        _table="_article_info_list",
        # 这里表示以 article_detail_url 为去重规则，若存在则更新，不存在则新增
        _mongo_update_rule={"article_detail_url": article_detail_url},
    )


# 其实，以上可以只赋值一次 AyuItem ，然后在 ITEM_PIPELINES 中激活对应的 pipelines 即可，这里是为了方便展示功能。
```

以上可知，目前可直接将需要的参数在对应 `Item` 中直接按 `key=value` 赋值即可，`key` 即为存储至库中字段，`value` 为存储内容。

当然，目前也支持动态赋值，但我还是推荐直接创建好 `AyuItem` ，方便管理：

```python
def parse(self, response):
    mdi = AyuItem(_table="table0")
    mdi.add_field("add_field1", "value1")
    mdi.add_field("add_field2", DataItem(key_value="value2"))
    mdi.add_field("add_field3", DataItem(key_value="value3", notes="add_field3值"))
    # _table 修改可通过以下方式，同样不推荐使用
    mdi["_table"] = "table1"


# 不允许 AyuItem 中字段值的类型（str 和 DataItem）混用，这里是用于示例展示。
```
注：在使用 `AyuItem` 时，其中各字段值（除了 `_mongo_update_rule`）的类型都要统一，比如要么都使用 `str` 类型，要么都使用 `DataItem` 类型。

另外，本库的 `item` 提供类型转换，以方便后续的各种使用场景：

```python
# 将本库 AyuItem 转为 dict 的方法
item_dict = mdi.asdict()
# 将本库 AyuItem 转为 scrapy Item 的方法
item = mdi.asitem()
```

## AyuItem 使用详解

> 详细介绍 `AyuItem` 支持的使用方法：

创建 `AyuItem` 实例：

```python
item = AyuItem(_table="ta")
```

获取字段：

```shell
>>> item["_table"]
'ta'
>>>
>>> # 注意：虽然也可以通过 item._table 的形式获取，但是不建议这样，显得不明了。
```

添加 / 修改字段（不存在则创建，存在则修改）：

```shell
>>> item["_table"] = "tab"
>>> item["title"] = "tit"
>>>
>>> # 也可通过 add_field 添加字段，但不能重复添加相同字段
>>> item.add_field("num", 10)
>>>
>>> [ item["_table"], item["title"], item["num"] ]
['tab', 'tit', 10]
```

类型转换：

```shell
>>> # 内置转为 dict 和 scrapy Item 的方法
>>>
>>> item.asdict()
{'title': 'tit', '_table': 'tab', 'num': 10}
>>>
>>> type(item.asitem())
<class 'ayugespidertools.items.ScrapyItem'>
```

删除字段：

```shell
>>> # 删除字段：
>>>
>>> del item["title"]
>>> item
{'_table': 'tab', 'num': 10}
```

## 使用示例

> 只需要在 `yield item` 时，按需提前导入 `AyuItem`，将所有的存储字段和场景补充字段全部添加完整即可。

`AyuItem` 在 `spider` 中常用的基础使用方法示例，以本库模板中的 `basic.tmpl` 为例来作解释：

```python
import json

from ayugespidertools.items import AyuItem, DataItem
from ayugespidertools.spiders import AyuSpider
from scrapy.http import Request
from scrapy.http.response.text import TextResponse
from sqlalchemy import text


class DemoOneSpider(AyuSpider):
    name = "demo_one"
    allowed_domains = ["csdn.net"]
    start_urls = ["https://www.csdn.net/"]
    custom_settings = {
        # 数据库引擎开关，打开会有对应的 engine 和 engine_conn，可用于数据入库前去重判断
        "DATABASE_ENGINE_ENABLED": True,
        "ITEM_PIPELINES": {
            # 激活此项则数据会存储至 Mysql
            "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
            # 激活此项则数据会存储至 MongoDB
            "ayugespidertools.pipelines.AyuFtyMongoPipeline": 301,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # 随机请求头
            "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
        },
    }

    def start_requests(self):
        """
        get 请求首页，获取项目列表数据
        """
        yield Request(
            url="https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=",
            callback=self.parse_first,
            headers={
                "referer": "https://blog.csdn.net/rank/list",
            },
            cb_kwargs={
                "curr_site": "csdn",
            },
            dont_filter=True,
        )

    def parse_first(self, response: TextResponse, curr_site: str):
        # 日志使用: scrapy 的 self.logger 或本库的 self.slog 或直接使用全局的 logger handle 也行（根据场景自行选择）
        self.slog.info(f"当前采集的站点为: {curr_site}")

        _save_table = "_article_info_list"
        # 你可以自定义解析规则，使用 lxml 还是 response.css response.xpath 等等都可以。
        data_list = json.loads(response.text)["data"]
        for curr_data in data_list:
            article_detail_url = curr_data.get("articleDetailUrl")
            article_title = curr_data.get("articleTitle")
            comment_count = curr_data.get("commentCount")
            favor_count = curr_data.get("favorCount")
            nick_name = curr_data.get("nickName")

            article_item = AyuItem(
                article_detail_url=DataItem(article_detail_url, "文章详情链接"),
                article_title=DataItem(article_title, "文章标题"),
                comment_count=DataItem(comment_count, "文章评论数量"),
                favor_count=DataItem(favor_count, "文章赞成数量"),
                nick_name=DataItem(nick_name, "文章作者昵称"),
                _table=DataItem(_save_table, "文章信息列表"),
                # 这里表示 MongoDB 存储场景以 article_detail_url 为去重规则，若存在则更新，不存在则新增
                _mongo_update_rule={"article_detail_url": article_detail_url},
            )
            self.slog.info(f"article_item: {article_item}")

            # 注意：同时存储至 mysql 和 mongodb 时，不建议使用以下去重方法，会互相影响。
            # 此时更适合：
            #    1.mysql 添加唯一索引去重（本库会根据 on duplicate key update 更新），
            #      mongoDB 场景下设置 _mongo_update_rule 参数即可；
            #    2.或者添加爬取时间字段并每次新增的场景，即不去重，请根据使用场景自行选择。
            # 这里只是为了介绍使用 mysql_engine / mysql_engine_conn 来对 mysql 去重的方法。
            if self.mysql_engine_conn:
                try:
                    _sql = text(
                        f"""select `id` from `{_save_table}` where `article_detail_url` = "{article_detail_url}" limit 1"""
                    )
                    result = self.mysql_engine_conn.execute(_sql).fetchone()
                    if not result:
                        self.mysql_engine_conn.rollback()
                        yield article_item
                    else:
                        self.slog.debug(f'标题为 "{article_title}" 的数据已存在')
                except Exception as e:
                    self.mysql_engine_conn.rollback()
                    yield article_item
            else:
                yield article_item
```

> 由上可知，本库中的 `Item` 使用方法还是很方便的。
>

**对以上 `Item` 相关信息解释：**

- 先导入所需 `Item`: `AyuItem`
- 构建对应场景的 `Item`
  - `Mysql` 存储场景需要配置 `_table` 参数
  - `MongoDB` 存储场景可能会需要 `_mongo_update_rule` 来设置去重的更新条件
- 最后 `yield` 对应 `item` 即可

## yield item

> 这里解释下 `item` 的格式问题，虽说也是支持直接 `yield dict` ，`scrapy` 的 `item` 格式(即本库中的 `ScrapyItem`)，还有就是本库推荐的 `AyuItem` 的形式。

这里介绍下 `item` 字段及其注释，以上所有 `item` 都有参数提示：

| item 字段              | 类型            | 注释                                                         |
| ---------------------- |---------------| ------------------------------------------------------------ |
| **自定义字段**         | DataItem，Any  | `item` 所有需要存储的字段，若有多个，请按规则自定义添加即可。 |
| **_table**             | DataItem, str | 存储至数据表或集合的名称。                                   |
| **_mongo_update-rule** | dict          | `MongoDB item` 场景下的查重规则。                            |
| **file_url**           | DataItem，Any  | `FilesDownloadPipeline` 文件下载场景时需要的下载链接参数。   |
| **file_format**        | DataItem，Any  | `FilesDownloadPipeline` 文件下载场景时需要的下载文件格式参数。 |

注，对以上表格中内容进行扩充解释：

- `file_url`，`file_format` 的字段只有在使用文件下载的场景时才需要设置，且对应的保存名称也会以 `_filename` 的新增字段添加到 `AyuItem` 中。
- 自定义字段使用示例请在 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/intro/tutorial.html) 中查看。

## 自定义 Item 字段和实现 Item Loaders

具体请在下一章浏览。
