# AyugeSpiderTools 一目了然

`AyugeSpiderTools` 是 `Scrapy` 的功能扩展模块，对其 `spider`，`item`，`middleware`，`pipeline` 等模块中的常用功能进行模板化生成和配置。比如生成常见的 `spider` ，运行 `sh` 和 `settings` 配置等脚本和固定项目文件结构；也对其不同模块进行功能扩展，比如给 `spider` 挂上 `Mysql engine` 的单例句柄可用于 `yield` 入库前的去重方式之一，给 `pipeline` 添加自动生成 `Mysql` 存储场景下所依赖的数据库、数据表、数据字段及注释，也可以解决常见的（字段编码，`Data too long`，存储字段不存在等等）错误场景。还有很多功能，请在其 `Github` 上查看。

> `AyugeSpiderTools` 相关信息：

```shell
 1. 具体请查看对应链接：[AyugeSpiderTools](https://github.com/shengchenyang/AyugeSpiderTools)
```

## 注意：

**如果你觉得某些功能实现未达到你的期望，比如某些中间件或管道等的实现方法你有更好的方式，你完全可以自行修改和 `build`，让其成为你个人或小组中的专属库。你可以修改任何你觉得有必要的部分，包括库名在内，希望本库能给你在爬虫开发或 `scrapy` 扩展开发方面有所指引。**

**当然，你也可以选择给此项目做出贡献，比如增加或优化某些功能等，但在此之前请提相关的 `ISSUES` 经确认后再开发和提交 `PULL REQUESTS`，以免不太符合本库场景或已废弃等原因造成你的贡献浪费，那就太可惜了！**

## 示例蜘蛛的演练

为了向您展示 `ayugespidertools` 带来了什么，我们将带您通过一个 `Scrapy Spider` 示例，使用最简单的方式来运行蜘蛛。

> 先创建项目：

```shell
# eg: 本示例使用的 project_name 为 DemoSpider

ayuge startproject <project_name>
```

> 创建爬虫脚本：

```shell
进入项目根目录
cd <project_name>

生成脚本
ayuge genspider <spider_name> <example.com>
```

下面是从网站 [https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=](https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=) 抓取热榜信息的蜘蛛代码：

```python
import json

from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.items import DataItem, MysqlDataItem
from ayugespidertools.spiders import AyuSpider
from scrapy.http import Request
from scrapy.http.response.text import TextResponse

from DemoSpider.items import TableEnum
from DemoSpider.settings import logger

"""
########################################################################################################################
# collection_website: CSDN - 专业开发者社区
# collection_content: 热榜文章排名 Demo 采集示例 - 存入 Mysql (配置根据本地 settings 的 LOCAL_MYSQL_CONFIG 中取值)
# create_time: 2022-07-30
# explain:
# demand_code_prefix = ""
########################################################################################################################
"""


class DemoOneSpider(AyuSpider):
    name = "demo_one"
    allowed_domains = ["blog.csdn.net"]
    start_urls = ["https://blog.csdn.net/"]

    # 数据库表的枚举信息，当前项目所依赖的表信息，一般用于存储数据时使用
    custom_table_enum = TableEnum
    # 初始化配置的类型，初始化设置（不需要直接不用配置）
    settings_type = 'debug'
    custom_settings = {
        # scrapy 日志等级
        'LOG_LEVEL': 'DEBUG',
        # 是否开启记录项目相关运行统计信息。不配置默认为 False
        "RECORD_LOG_TO_MYSQL": True,
        # 设置 ayugespidertools 库的日志输出为 loguru，可自行配置 logger 规则来管理项目日志。若不配置此项，库日志只会在控制台上打印
        "LOGURU_CONFIG": logger,
        "ITEM_PIPELINES": {
            # 激活此项则数据会存储至 Mysql
            "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # 随机请求头
            "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
        },
    }

    # 打开 mysql 引擎开关，用于数据入库前更新逻辑判断
    mysql_engine_enabled = True

    def start_requests(self):
        """
        获取项目热榜的列表数据
        """
        yield Request(
            url="https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=",
            callback=self.parse_first,
            headers={
                "referer": "https://blog.csdn.net/rank/list",
            },
            dont_filter=True,
        )

    def parse_first(self, response: TextResponse):
        data_list = json.loads(response.text)["data"]
        for curr_data in data_list:
            # 这里的所有解析方式可选择自己习惯的其它任意库，xpath， json 或正则等等。
            article_detail_url = ToolsForAyu.extract_with_json(
                json_data=curr_data, query="articleDetailUrl"
            )

            article_title = ToolsForAyu.extract_with_json(
                json_data=curr_data, query="articleTitle"
            )

            comment_count = ToolsForAyu.extract_with_json(
                json_data=curr_data, query="commentCount"
            )

            favor_count = ToolsForAyu.extract_with_json(
                json_data=curr_data, query="favorCount"
            )

            nick_name = ToolsForAyu.extract_with_json(
                json_data=curr_data, query="nickName"
            )

            # 数据存储方式 1，需要添加注释时的写法
            ArticleInfoItem = MysqlDataItem(
                # 这里也可以写为 article_detail_url = DataItem(article_detail_url)，但没有注释
                # 功能了，那不如使用下面的数据存储方式 2
                article_detail_url=DataItem(article_detail_url, "文章详情链接"),
                article_title=DataItem(article_title, "文章标题"),
                comment_count=DataItem(comment_count, "文章评论数量"),
                favor_count=DataItem(favor_count, "文章赞成数量"),
                nick_name=DataItem(nick_name, "文章作者昵称"),
                _table=TableEnum.article_list_table.value["value"],
            )

            # 数据存储方式 2，若不需要注释，也可以这样写，但不要两种风格混用
            """
            ArticleInfoItem = MysqlDataItem(
                article_detail_url=article_detail_url,
                article_title=article_title,
                comment_count=comment_count,
                favor_count=favor_count,
                nick_name=nick_name,
                _table=TableEnum.article_list_table.value["value"],
            )
            """
            self.slog.info(f"ArticleInfoItem: {ArticleInfoItem}")
            # yield ArticleInfoItem

            # 数据入库逻辑 -> 测试 mysql_engine 的去重功能，你可以自行实现。mysql_engine 也已经给你了
            save_table = TableEnum.article_list_table.value["value"]
            sql = f"""select `id` from `{save_table}` where `article_detail_url` = "{article_detail_url}" limit 1"""
            yield ToolsForAyu.filter_data_before_yield(
                sql=sql,
                mysql_engine=self.mysql_engine,
                item=ArticleInfoItem,
            )
```

### 刚刚发生了什么？

刚刚使用 `ayugespidertools` 创建了项目，并生成了具体的爬虫脚本示例。其爬虫脚本中的各种依赖（比如项目目录结构，配置信息等）在创建项目后就正常产生了，一般所需的配置信息（比如 `Mysql`，`MongoDB`，`OSS` 等）在项目的 `VIT` 目录下 `.conf` 文件中修改，不需要配置的不用理会它即可。

只要配置好 `.conf` 信息，就可以跑通以上示例。如果修改为新的项目，只需要修改上面示例中的 `spdider` 解析规则即可。

## 还有什么？

本库依赖 `Scrapy`，你可以使用 `Scrapy` 命令来管理你的项目，体会 `Scrapy` 的强大和方便。

`ayugespidertools` 根据 `scrapy` 的模板功能方便的创建示例脚本，比如：

```shell
# 查看支持的脚本模板示例
ayuge genspider -l

<output>
Available templates:
  async
  basic
  crawl
  csvfeed
  xmlfeed

# 使用具体的示例命令
ayuge genspider -t <Available_templates> <spider_name> <example.com>

eg: ayuge gendpier -t async demom_async baidu.com
```

## 下一步是什么？

接下来的步骤是 [安装 AyugeSpiderTools](https://docs.scrapy.org/en/latest/intro/install.html#intro-install)， [按照 Scrapy 的教程](https://docs.scrapy.org/en/latest/intro/tutorial.html#intro-tutorial)学习如何使用 `Scrapy` 并[加入 Scrapy 社区](https://scrapy.org/community/)。谢谢你的关注！
