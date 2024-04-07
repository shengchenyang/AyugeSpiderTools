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
ayuge startproject DemoSpider
```

这将创建一个 `DemoSpider` 包含以下内容的目录：

通常情况下，我们只需关心 `spider` 的编写和 `VIT` 中 `.conf` 的配置即可。

```ini
DemoSpider/
|-- DemoSpider			# project's Python module, you'll import your code from here
|   |-- __init__.py
|   |-- items.py		# project items definition file
|   |-- logs			# 日志管理文件夹，可以自定义规则
|   |   |-- DemoSpider.log	# scrapy 输出日志，文件名称为项目名
|   |   |-- error.log		# loguru 日志 error 规则输出文件
|   |-- middlewares.py		# project middlewares definition file
|   |-- pipelines.py		# project pipelines definition file
|   |-- run.py			# scrapy 运行文件
|   |-- run.sh			# 项目运行 shell，运行以上的 run.py，win 平台不会生成此文件
|   |-- settings.py		# project settings definition file
|   |-- spiders			# a directory where you'll later put your spiders
|   |   |-- __init__.py
|   `-- VIT
|       `-- .conf        	# 配置文件，用于修改 Mysql, MongoDB 等配置
|-- README.md			# 说明文档
|-- requirements.txt		# 依赖文件
`-- scrapy.cfg                  # deploy configuration file
```

## 我们的第一个 Spider

这是我们第一个 `Spider` 的代码。`demo_one.py` 将其保存在项目目录下命名的文件 `DemoSpider/spiders`中：

```python
import json

from ayugespidertools.items import AyuItem
from ayugespidertools.spiders import AyuSpider
from scrapy.http import Request


class DemoEightSpider(AyuSpider):
    name = "demo_eight"
    allowed_domains = ["blog.csdn.net"]
    start_urls = ["https://blog.csdn.net/"]
    custom_settings = {
        # 打开 mysql 引擎开关，用于数据入库前更新逻辑判断
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
            dont_filter=True,
        )

    def parse_first(self, response):
        data_list = json.loads(response.text)["data"]
        for curr_data in data_list:
            article_detail_url = curr_data.get("articleDetailUrl")
            article_title = curr_data.get("articleTitle")
            comment_count = curr_data.get("commentCount")
            favor_count = curr_data.get("favorCount")
            nick_name = curr_data.get("nickName")

            article_item = AyuItem(
                article_detail_url=article_detail_url,
                article_title=article_title,
                comment_count=comment_count,
                favor_count=favor_count,
                nick_name=nick_name,
                _table="_article_info_list",
            )
            yield article_item
```

如您所见，`Spider` 子类化 `AyuSpider` 并定义了一些属性和方法：

- `name`: 标识蜘蛛。在一个项目中必须是唯一的，即不能为不同的Spiders设置相同的名字。
- `start_requests()`: 必须返回一个可迭代的请求（你可以返回一个请求列表或编写一个生成器函数），蜘蛛将从中开始爬行。后续请求将从这些初始请求中依次生成。
- `parse_first()`：将被调用以处理为每个请求下载的响应的方法。`response` 参数是 `TextResponse` 的一个实例，它保存页面内容，并有进一步的有用方法来处理它。该 `parse_first()` 方法通常解析响应，将抓取的数据提取为字典，并找到要遵循的新 URL 并从中创建新请求 ( `Request`)。

另外，一些其它注意事项：

- 示例中的一些配置和一些功能并不是每个项目中都必须要编写和配置的，只是用于展示一些功能
- 据上条可知，可以写出很简洁的代码，删除你认为的无关配置和方法并将其配置成你自己的模板就更容易适配更多人的使用场景。


### 如何运行我们的蜘蛛

要让我们的蜘蛛工作，请转到项目的顶级目录并运行：

```shell
# 本身就是 scrapy 的项目，所以可以使用 scrapy 可以执行的任何形式即可
scrapy crawl demo_one

# 或者执行项目根目录下的 run.py(需要编辑自己需要执行的脚本)
python run.py

# 或者执行项目根目录下的 run.sh，其实它也是通过调用 run.py 来执行的。只不过 shell 文件中包含了虚拟环境的 activate 了而已
sh run.sh
```
