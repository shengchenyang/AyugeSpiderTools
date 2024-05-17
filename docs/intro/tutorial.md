# AyugeSpiderTools 教程

在本教程中，我们假设您的系统上已经安装了 `ayugespidertools`。

> 我们要抓取 [ayugespidertools readthedocs](https://ayugespidertools.readthedocs.io/en/latest/) 的网页内容，这是本库的文档网站。
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

这是我们第一个 `Spider` 的代码 `demo_one.py` ，将其保存在项目目录下命名的文件 `DemoSpider/spiders`中：

```python
from ayugespidertools.items import AyuItem
from ayugespidertools.spiders import AyuSpider
from scrapy.http import Request


class DemoOneSpider(AyuSpider):
    name = "demo_one"
    allowed_domains = ["readthedocs.io"]
    start_urls = ["http://readthedocs.io/"]
    custom_settings = {
        # 打开 mysql 引擎开关，用于数据入库前更新逻辑判断
        "DATABASE_ENGINE_ENABLED": True,
        "ITEM_PIPELINES": {
            # 激活此项则数据会存储至 Mysql
            "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
            # 激活此项则数据会存储至 MongoDB
            "ayugespidertools.pipelines.AyuFtyMongoPipeline": 301,
        },
    }

    def start_requests(self):
        yield Request(
            url="https://ayugespidertools.readthedocs.io/en/latest/",
            callback=self.parse_first,
        )

    def parse_first(self, response):
        _save_table = "_octree_info"

        li_list = response.xpath('//div[@aria-label="Navigation menu"]/ul/li')
        for curr_li in li_list:
            octree_text = curr_li.xpath("a/text()").get()
            octree_href = curr_li.xpath("a/@href").get()

            octree_item = AyuItem(
                octree_text=octree_text,
                octree_href=octree_href,
                _table=_save_table,
            )
            self.slog.info(f"octree_item: {octree_item}")
            yield octree_item
```

如您所见，`Spider` 子类化 `AyuSpider` 并定义了一些属性和方法：

- `name`: 标识蜘蛛。在一个项目中必须是唯一的，即不能为不同的 `Spiders` 设置相同的名字。
- `start_requests()`: 必须返回一个可迭代的请求（你可以返回一个请求列表或编写一个生成器函数），蜘蛛将从中开始爬行。后续请求将从这些初始请求中依次生成。
- `parse_first()`：将被调用以处理为每个请求下载的响应的方法。`response` 参数是 `TextResponse` 的一个实例，它保存页面内容，并有进一步的有用方法来处理它。该 `parse_first()` 方法通常解析响应，将抓取的数据提取为字典，并找到要遵循的新 `URL` 并从中创建新请求 ( `Request`)。

另外，一些其它注意事项：

- 示例中的一些配置和一些功能并不是每个项目中都必须要编写和配置的，只是用于展示一些功能；
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
