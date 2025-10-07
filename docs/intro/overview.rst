.. _intro-overview:

===========================
AyugeSpiderTools 一目了然
===========================

`AyugeSpiderTools`_ 是 Scrapy 的功能扩展模块，对其 spider，item，middleware，pipeline 等模块中\
的常用功能进行模板化生成和配置。比如生成常见的 spider，运行 sh 和 settings 配置等脚本和固定项目文件结\
构；也对其不同模块进行功能扩展，比如给 spider 挂上 Mysql engine 的单例句柄可用于 yield 入库前的去重\
方式之一；给 pipeline 添加自动生成 Mysql 存储场景下所依赖的数据库、数据表、数据字段及注释，也可以解决常\
见的（字段编码，Data too long，存储字段不存在等的）错误场景；去除 item 的 scrapy.Field 定义，可直接\
在 spider 中动态赋值 item，且当 spider 中 item 变动后不用关心去对照修改 pipeline 字段部分。还有更多\
功能，请在 Github 上查看。

.. note::

   如果你觉得某些功能实现未达到你的期望，比如某些中间件或管道等的实现方法你有更好的方式，你完全可以自行修\
   改和 build，让其成为你个人或小组中的专属库。你可以修改任何你觉得有必要的部分，包括库名在内，希望本库\
   能给你在爬虫开发或 scrapy 扩展开发方面有所指引。

   当然，你也可以选择给此项目做出贡献，比如增加或优化某些功能等，但在此之前请提相关的 ISSUES 经确认后再\
   开发和提交 PULL REQUESTS，以免不太符合本库场景或已废弃等原因造成你的贡献浪费，那就太可惜了！

示例蜘蛛的演练
===============

为了向您展示 ayugespidertools 带来了什么，我们将带您通过一个 Scrapy Spider 示例，使用最简单的方式来\
运行蜘蛛。

先创建项目：
::

   # eg: 本示例使用的 project_name 为 DemoSpider
   ayuge startproject <project_name>

创建爬虫脚本：
::

   进入项目根目录
   cd <project_name>

生成脚本:
::

   ayuge genspider <spider_name> <example.com>


下面是从 `AyugeSpiderTools`_ 文档网页中抓取标题信息的蜘蛛代码：

.. code-block:: python

   from __future__ import annotations

   from typing import TYPE_CHECKING, Any

   from ayugespidertools.items import DataItem, AyuItem
   from ayugespidertools.spiders import AyuSpider
   from scrapy.http import Request
   from sqlalchemy import text

   if TYPE_CHECKING:
       from collections.abc import AsyncIterator

       from scrapy.http import Response


   class DemoOneSpider(AyuSpider):
       name = "demo_one"
       allowed_domains = ["readthedocs.io"]
       start_urls = ["http://readthedocs.io/"]
       custom_settings = {
           "ITEM_PIPELINES": {
               # 激活此项则数据会存储至 Mysql
               "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
           },
       }

       async def start(self) -> AsyncIterator[Any]:
           yield Request(
               url="https://ayugespidertools.readthedocs.io/en/latest/",
               callback=self.parse_first,
           )

       def parse_first(self, response: Response) -> Any:
           _save_table = "_octree_info"
           li_list = response.xpath('//div[@aria-label="Navigation menu"]/ul/li')
           for curr_li in li_list:
               octree_text = curr_li.xpath("a/text()").get()
               octree_href = curr_li.xpath("a/@href").get()

               # NOTE: 数据存储方式 1，推荐此风格写法。
               octree_item = AyuItem(
                   octree_text=octree_text,
                   octree_href=octree_href,
                   _table=_save_table,
                   # 若不使用内置去重更新功能，就不需要设置以下参数
                   _update_rule={"octree_text": octree_text},
                   _update_keys={"octree_href"},
               )

               # NOTE: 数据存储方式 2，需要自动添加表字段注释时的写法。但不要风格混用。
               """
               octree_item = AyuItem(
                   # 这里也可以写为 octree_text = DataItem(octree_text)，但没有字段注释
                   # 功能了，那不如使用 <数据存储方式 1>
                   octree_text=DataItem(octree_text, "标题"),
                   octree_href=DataItem(octree_href, "标题链接"),
                   _table=DataItem(_save_table, "项目列表信息"),
               )
               """

               # NOTE: 数据存储方式 3，当然也可以直接 yield dict
               # 但 _table，_update_rule，_update_keys 等内置参数就没有 IDE 提示功能了
               """
               yield {
                   "octree_text": octree_text,
                   "octree_href": octree_href,
                   "_table": _save_table,
               }
               """
               self.slog.info(f"octree_item: {octree_item}")
               yield octree_item

刚刚发生了什么？
----------------

刚刚使用 `ayugespidertools` 创建了项目，并生成了具体的爬虫脚本示例。其爬虫脚本中的各种依赖（比如项目\
目录结构，配置信息等）在创建项目后就正常产生了，一般所需的配置信息（比如 `Mysql`，`MongoDB` 等）在项目\
的 `VIT` 目录下 `.conf` 文件中修改，不需要配置的不用理会它即可。

只要配置好 `.conf` 信息，就可以跑通以上示例。如果修改为新的项目，只需要修改上面示例中的 `spdider` 解析\
规则即可。

.. note::

   本库中提供了 sqlalchemy 来对 spider 中 mysql，postgresql 和 oracle 的入库前的去重查询，但是未\
   提供支持异步场景。这里只是用于简单场景的使用，如果你需要更加自定义的复杂场景，那么你需要在 spider 中\
   直接只使用 ``self.mysql_conf``，``self.postgres_conf``，``self.oracle_conf`` 等，或者结合\
   `custom_section`_ 的自定义配置创建对应的数据库连接来达到入库前去重的场景，这样你就可以选择自己喜欢\
   的工具，不再局限于 sqlalchemy。

   本库不会增加 sqlalchemy 的异步支持了，会使得项目臃肿，``self.mysql_conf`` 和 ``custom_section`` \
   的方式已经可以很简单优雅地实现你想要的去重要求了。或者你可以考虑基于文件的去重、``scrapy-redis`` 库或 \
   ``rabbitmq`` 的任务分发等方式来解决去重方式。

   本库在 3.12.0 版本添加了链接到各种数据库的方法，以方便用户创建对应数据库场景的链接来自定义去重功能。\
   具体使用方法请在 `DemoSpider`_ 中查看。

还有什么？
===========

本库依赖 Scrapy，你可以使用 Scrapy 命令来管理你的项目，体会 Scrapy 的强大和方便。

ayugespidertools 根据 scrapy 的模板功能方便的创建示例脚本，比如：
::

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

下一步是什么？
==============

接下来的步骤是 :ref:`安装 AyugeSpiderTools <intro-install>`， 按照 `Scrapy 教程`_ 学习如何使用 \
Scrapy 并加入 `Scrapy 社区`_ 。谢谢你的关注！

.. _AyugeSpiderTools: https://github.com/shengchenyang/AyugeSpiderTools
.. _Scrapy 教程: https://docs.scrapy.org/en/latest/intro/tutorial.html#intro-tutorial
.. _DemoSpider: https://github.com/shengchenyang/DemoSpider
.. _custom_section: https://ayugespidertools.readthedocs.io/en/latest/topics/configuration.html#custom-section
.. _Scrapy 社区: https://scrapy.org/community/
