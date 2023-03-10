# AyugeSpiderTools 一目了然

`AyugeSpiderTools` 是一个对 `Scrapy` 扩展模块，对其 `spider`，`item`，`middleware`，`pipeline` 等模块中的常用功能进行模板化生成和配置。比如使用生成常见的 `spider` ，运行 `sh` 和 `settings` 配置等脚本和固定项目文件结构，也对其不同模块功能扩展，比如给 `spider` 挂上 `Mysql engine` 的单例句柄用于 `yield` 前的去重逻辑，给 `pipeline` 添加自动生成 `Mysql` 存储场景下所依赖的数据库、数据表、数据字段及注释，也可以解决常见的（字段编码，`Data too long`，存储字段不存在等等）错误场景。还有很多功能，请在其 `Github` 上查看。

> `AyugeSpiderTools` 相关信息：

```shell
 1. 具体请查看对应链接：[AyugeSpiderTools](https://github.com/shengchenyang/AyugeSpiderTools)
```

## 注意：

**如果你觉得某些功能实现未达到你的期望，比如某些中间件或管道等的实现方法你有更好的方式，你完全可以自行修改和 `build`，让其成为你个人或小组中的专属库。你可以修改任何你觉得有必要的部分，包括库名在内，希望本库能给你在爬虫开发或 `scrapy` 扩展开发方面有所指引。**

## 示例蜘蛛的演练

为了向您展示 `ayugespidertools` 带来了什么，我们将带您通过一个 `Scrapy Spider` 示例，使用最简单的方式来运行蜘蛛。

**注意：若你觉得 `ayugespidertools` 的 `cli` 名称过长，你可以使用 `ayuge` 来替代。** 

> 先创建项目：

```shell
# eg: 本示例使用的 project_name 为 DemoSpider

ayugespidertools startproject <project_name>

# 也可使用以下命令代替：
ayuge startproject <project_name>
```

> 创建爬虫脚本：

```shell
进入项目根目录
cd <project_name>

生成脚本
ayugespidertools genspider <spider_name> <example.com>

# 也可使用以下命令代替：
ayuge genspider <spider_name> <example.com>
```

下面是从网站 [https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=](https://blog.csdn.net/phoenix/web/blog/hot-rank?page=0&pageSize=25&type=) 抓取热榜信息的蜘蛛代码：

```python
import json
from scrapy.http import Request
from ayugespidertools.Items import DataItem, MysqlDataItem
from DemoSpider.common.DataEnum import TableEnum
from ayugespidertools.AyugeSpider import AyuSpider
from ayugespidertools.common.Utils import ToolsForAyu

"""
####################################################################################################
# collection_website: CSDN - 专业开发者社区
# collection_content: 热榜文章排名 Demo 采集示例 - 存入 Mysql (配置根据本地 settings 的 LOCAL_MYSQL_CONFIG 中取值)
# create_time: 2022-07-30
# explain:
# demand_code_prefix = ''
####################################################################################################
"""


class DemoOneSpider(AyuSpider):
    name = 'demo_one'
    allowed_domains = ['blog.csdn.net']
    start_urls = ['https://blog.csdn.net/']

    # 数据库表的枚举信息，当前项目所依赖的表信息，一般用于存储数据时使用
    custom_table_enum = TableEnum
    # 初始化配置的类型，初始化设置
    settings_type = 'debug'
    custom_settings = {
        # 日志等级，此参数值与 ayugespidertools 库中的 loguru 日志等级一致
        'LOG_LEVEL': 'DEBUG',
        # 是否开启记录项目相关运行统计信息，其实默认就是关闭，为了展示此参数
        'RECORD_LOG_TO_MYSQL': False,
        # Mysql 数据表的前缀名称，用于标记属于哪个项目（也可不配置此参数，按需配置）
        'MYSQL_TABLE_PREFIX': "demo1_",
        'ITEM_PIPELINES': {
            # 激活此项则数据会存储至 Mysql，其 Mysql 链接配置在 VIT 目录下的 .conf 中查看
            'ayugespidertools.Pipelines.AyuFtyMysqlPipeline': 300,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 随机请求头，请求头优先级与 `fake_useragent` 中的一致
            'ayugespidertools.Middlewares.RandomRequestUaMiddleware': 400,
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
                'referer': 'https://blog.csdn.net/rank/list',
            },
            dont_filter=True
        )

    def parse_first(self, response):
        data_list = json.loads(response.text)['data']
        for curr_data in data_list:
            # 这里的所有解析规则可选择自己习惯的
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

            # 数据存储方式1，非常推荐此写法。article_info 含有所有需要存储至表中的字段
            article_info = {
                "article_detail_url": DataItem(article_detail_url, "文章详情链接"),
                "article_title": DataItem(article_title, "文章标题"),
                "comment_count": DataItem(comment_count, "文章评论数量"),
                "favor_count": DataItem(favor_count, "favor_count"),
                "nick_name": DataItem(nick_name, "文章作者昵称"),
            }

            """
            # 当然这么写也可以，但是不推荐
            article_info = {
                "article_detail_url": {
                    "key_value": article_detail_url,
                    "notes": "文章详情链接",
                },
                "article_title": {
                    "key_value": article_title,
                    "notes": "文章标题",
                },
                "comment_count": {
                    "key_value": comment_count,
                    "notes": "文章评论数量",
                },
                "favor_count": {
                    "key_value": favor_count,
                    "notes": "文章赞成数量",
                },
                "nick_name": {
                    "key_value": nick_name,
                    "notes": "文章作者昵称",
                },
            }
            
            # 或者这么写，也不推荐
            article_info = {
                "article_detail_url": article_detail_url,
                "article_title": article_title,
                "comment_count": comment_count,
                "favor_count": favor_count,
                "nick_name": nick_name,
            }
            """

            ArticleInfoItem = MysqlDataItem(
                alldata=article_info,
                table=TableEnum.aritle_list_table.value['value'],
            )

            # 数据入库逻辑 -> 测试 mysql_engine 的去重功能
            try:
                sql = '''select `id` from `{}` where `article_detail_url` = "{}" limit 1'''.format(self.custom_settings.get('MYSQL_TABLE_PREFIX', '') + TableEnum.aritle_list_table.value['value'], article_detail_url)
                df = pandas.read_sql(sql, self.mysql_engine)

                # 如果为空，说明此数据不存在于数据库，则新增
                if df.empty:
                    yield ArticleInfoItem

                # 如果已存在，1). 若需要更新，请自定义更新数据结构和更新逻辑；2). 若不用更新，则跳过即可。
                else:
                    logger.debug(f"标题为 ”{article_title}“ 的数据已存在")

            except Exception:
                yield ArticleInfoItem
```

### 刚刚发生了什么？

刚刚使用 `ayugespidertools` 创建了项目，并生成了具体的爬虫脚本示例。其爬虫脚本中的各种依赖（比如项目目录结构，配置信息等）在创建项目后就正常产生了，一般所需的配置信息（比如 `Mysql`，`MongoDB`，`OSS` 等）在项目的 `VIT` 目录下 `.conf` 文件中修改，不需要配置的不用理会它即可。

只要配置好 `.conf` 信息，就可以跑通以上示例。如果修改为新的项目，只需要修改上面示例中的 `spdider` 解析规则即可。

## 还有什么？

本库依赖 `Scrapy`，你可以使用 `Scrapy` 命令来管理你的项目，体会 `Scrapy` 的强大和方便。

`ayugespidertools` 根据 `scrapy` 的模板功能方便的创建示例脚本，比如：

```shell
# 查看支持的脚本模板示例
ayugespidertools genspider -l

<output>
Available templates:
  async
  basic
  crawl
  csvfeed
  xmlfeed

# 使用具体的示例命令(都可以使用 `ayuge cli` 名称代替)
ayugespidertools genspider -t <Available_templates> <spider_name> <example.com>

eg: ayugespidertools gendpier -t async demom_async baidu.com
```

## 下一步是什么？

接下来的步骤是 [安装 AyugeSpiderTools](https://docs.scrapy.org/en/latest/intro/install.html#intro-install)， [按照 Scrapy 的教程](https://docs.scrapy.org/en/latest/intro/tutorial.html#intro-tutorial)学习如何使用 `Scrapy` 并[加入 Scrapy 社区](https://scrapy.org/community/)。谢谢你的关注！
