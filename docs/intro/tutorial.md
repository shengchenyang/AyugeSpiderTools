# AyugeSpiderTools 教程

在本教程中，我们假设您的系统上已经安装了 `ayugespidertools`。

> 我们要抓取 [blog.csdn.net](https://blog.csdn.net/)，这是一个知识问答社区的网站。
>

本教程将引导您完成这些任务：

- 创建一个新的 `Scrapy` 项目
- 编写爬虫来抓取站点并提取数据
- 使用命令行导出抓取的数据
- 更改蜘蛛以递归地跟踪链接
- 使用蜘蛛参数

## 创建项目

在开始抓取之前，您必须设置一个新的 `ayugespidertools` 项目。输入您要存储代码的目录并运行：

```shell
ayugespidertools startproject DemoSpider
```

这将创建一个 `DemoSpider` 包含以下内容的目录：

```ini
DemoSpider/
|-- DemoSpider								# project's Python module, you'll import your code from here
|   |-- common								# 这里主要存放通用方法，自定义方法模块。
|   |   |-- DataEnum.py						# 数据库表枚举信息示例
|   |-- __init__.py
|   |-- items.py							# project items definition file
|   |-- logs								# 日志管理文件夹，可以自定义规则
|   |   |-- DemoSpider.log					# scrapy 输出日志，文件名称为项目名
|   |   |-- error.log						# loguru 日志 error 规则输出文件
|   |   `-- runtime.log						# loguru 日志 debug 规则输出文件
|   |-- middlewares.py						# project middlewares file
|   |-- pipelines.py						# project pipelines file
|   |-- run.py								# scrapy 运行文件
|   |-- run.sh								# 项目运行 shell，运行以上的 run.py
|   |-- settings.py							# project settings file
|   |-- spiders								# a directory where you'll later put your spiders
|   |   |-- __init__.py
|   `-- VIT
|       `-- 请修改.conf中的配置信息			  # 提示文件
| 		`-- .conf							# 配置文件，用于修改 Mysql, MongoDB 等配置
|-- .gitignore								# git ignore 文件
|-- pyproject.toml							# 项目配置
|-- README.md								# 说明文档
|-- requirements.txt						# 依赖文件
`-- scrapy.cfg                              # deploy configuration file
```

## 我们的第一个 Spider

这是我们第一个 `Spider` 的代码。`demo_one.py`将其保存在项目目录下命名的文件 `DemoSpider/spiders`中：

```python
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
# collection_website: CSDN - 专业开发者社区
# collection_content: 热榜文章排名 Demo 采集示例 - 同时存入 Mysql 和 MongoDB 的场景 (配置根据本地 settings 的中取值)
# create_time: 2023-01-10
# explain:
# demand_code_prefix = ''
####################################################################################################
"""


class DemoOneSpider(AyuSpider):
    name = 'demo_one'
    allowed_domains = ['blog.csdn.net']
    start_urls = ['https://blog.csdn.net/']

    # 数据库表的枚举信息
    custom_table_enum = TableEnum
    # 初始化配置的类型
    settings_type = 'debug'
    custom_settings = {
        # scrapy 日志等级配置
        'LOG_LEVEL': 'DEBUG',
        'LOGURU_ENABLED': False,
        # 是否开启记录项目相关运行统计信息。不配置默认为 False
        'RECORD_LOG_TO_MYSQL': False,
        # 设置 ayugespidertools 库的日志输出为 loguru，可自行配置 logger 规则来管理项目日志。若不配置此项，库日志只会在控制台上打印
        'LOGURU_CONFIG': logger,
        # Mysql数据表的前缀名称，用于标记属于哪个项目，也可以不用配置
        'MYSQL_TABLE_PREFIX': "demo_basic_",
        # MongoDB 集合的前缀名称，用于标记属于哪个项目，也可以不用配置
        'MONGODB_COLLECTION_PREFIX': "demo_basic_",
        'ITEM_PIPELINES': {
            # 激活此项则数据会存储至 Mysql
            'ayugespidertools.Pipelines.AyuFtyMysqlPipeline': 300,
            # 激活此项则数据会存储至 MongoDB
            'ayugespidertools.Pipelines.AyuFtyMongoPipeline': 301,
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
            cb_kwargs=dict(
                curr_site="csdn",
            ),
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

            self.slog.error(f"test {nick_name}")
            # 这是 MongoDB 存储场景的示例
            AritleInfoMongoItem = MongoDataItem(
                # alldata 用于存储 mongo 的 Document 文档所需要的字段映射
                alldata=article_info,
                # table 为 mongo 的存储 Collection 集合的名称
                table=TableEnum.article_list_table.value['value'],
                # mongo_update_rule 为查询数据是否存在的规则
                mongo_update_rule={"article_detail_url": article_detail_url},
            )
            yield AritleInfoMongoItem
```

如您所见，我们的 `Spider` 子类化`AyugeSpider.AyuSpider` 并定义了一些属性和方法：

- `name`: 标识蜘蛛。在一个项目中必须是唯一的，即不能为不同的Spiders设置相同的名字。
- `start_requests()`: 必须返回一个可迭代的请求（你可以返回一个请求列表或编写一个生成器函数），蜘蛛将从中开始爬行。后续请求将从这些初始请求中依次生成。
- `parse_first()`：将被调用以处理为每个请求下载的响应的方法。`response` 参数是 `TextResponse` 的一个实例，它保存页面内容，并有进一步的有用方法来处理它。该 `parse_first()` 方法通常解析响应，将抓取的数据提取为字典，并找到要遵循的新 URL 并从中创建新请求 ( `Request`)。

### 如何运行我们的蜘蛛

要让我们的蜘蛛工作，请转到项目的顶级目录并运行：

```shell
# 本身就是 scrapy 的项目，所以可以使用 scrapy 可以执行的任何形式即可
scrapy crawl demo_one

# 或者执行项目根目录下的 run.py(需要编辑自己需要执行的脚本)
python3 run.py

# 或者执行项目根目录下的 run.sh，其实它也是通过调用 run.py 来执行的。只不过 shell 文件中包含了虚拟环境的 activate 了而已
sh run.sh
```
