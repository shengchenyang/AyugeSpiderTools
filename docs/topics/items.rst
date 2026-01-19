.. _topics-items:

====
Item
====

演示在使用本库场景下 Item 的使用方法，文档中所有 item 也都是指本库的 AyuItem 模块，除非有特意标明为其\
它库的 item。

本教程将引导您完成这些任务：

- 演示本库推荐的 AyuItem 适配方式
- 补充适配 add_value, add_xpath, add_css 等方法的示例

快速开始
==========

scrapy 中 Item 对应本库的 AyuItem，AyuItem 可用 ``AyuItem(key=value)`` 的形式直接动态赋值，其中 \
value 介绍如下：

value 可选择的类型有：

- 普通字段

.. code-block:: python

   from ayugespidertools.items import AyuItem

   _title = "article_title_value"
   demo_item = AyuItem(article_title=_title)

- ``DataItem`` 字段

  - 完整赋值

.. code-block:: python

   # `DataItem` 有 `key_value` 和 `notes` 两个参数，`key_value` 为存储的值；
   # `notes` 在 `ElasticSearch` 存储场景中表示 `es document fields`，在其他(需要字段
   # 注释时，比如 `Mysql`，`postgresql` 存储)场景中表示为字段注释。

   # 普通场景
   demo_item = AyuItem(
       article_title=DataItem(_title, "文章标题"),
   )

   # es 场景
   from elasticsearch_dsl import Keyword

   demo_item = AyuItem(
       article_title=DataItem(_title, Keyword()),
   )

---------------------------------------------------

  - 无 ``notes`` 赋值

.. code-block:: python

   # 即不需要字段注释，也不是 es 存储场景下，只赋值 key_value 参数

   demo_item = AyuItem(
       article_title=DataItem(_title),
   )

   # 不过，这种写法风格不如直接使用 【普通字段】的优雅赋值方式。

.. note::

   不要在非同步的 mysql，postgresql 存储场景下使用 DataItem，DataItem 只在 es 存储场景下有特定的功\
   能，且在同步的 mysql，postgresql 存储场景下有创建表及字段的作用，其它场景则无任何作用甚至会报错。

实现原理
==========

以下为 Mysql， MongoDB 和 ElasticSearch 存储时的 AyuItem 示例，其它场景的用法也都一样：

本库将所有需要存储的字段直接在对应的 Item (AyuItem) 中赋值即可，其中 ``_table`` 参数为必须参数，也可\
以使用 ``add_field`` 方法动态添加字段。

.. code-block:: python

   _save_table = "_article_info_list"


   def parse(self, response):
       # 存储到 Mysql，mongodb，postgresql，oracle 场景时 Item 构建示例：
       article_mysql_item = AyuItem(
           article_detail_url=article_detail_url,
           article_title=article_title,
           comment_count=comment_count,
           favor_count=favor_count,
           nick_name=nick_name,
           _table=_save_table,
           # 若不使用内置去重更新功能，就不需要设置以下参数
           _update_rule={"article_title": article_title},
           _update_keys={"comment_count", "favor_count"},
           # postgresql 去重更新场景才需要设置的唯一索引约束
           _conflict_cols={"article_title"},
       )

       # 存储到 ElasticSearch 场景时 Item 构建示例：
       # 同样地，为保持风格统一，es 存储场景中会把 es Document 中 fields 的声明
       # 放在 AyuItem 中 DataItem 的 notes 参数中。
       # 这个参数在其他(需要字段注释，比如 Mysql，postgresql)场景中表示为字段注释。
       from elasticsearch_dsl import Keyword, Search, Text

       book_info_item = AyuItem(
           book_name=DataItem(
               book_name, Text(analyzer="snowball", fields={"raw": Keyword()})
           ),
           book_href=DataItem(book_href, Keyword()),
           book_intro=DataItem(book_intro, Keyword()),
           _table=DataItem(_save_table, "这里的索引注释可有可无，程序中不会使用。"),
       )


   # 具体不同的场景示例，请在 DemoSpider 项目中查看；
   # 如非场景需要，不推荐使用 DataItem 的方式构建 AyuItem，不太优雅。

以上可知，目前可直接将需要的参数在对应 Item 中直接按 ``key=value`` 赋值即可，key 为存储至库中字段，\
value 为对应 key 所存储的值。

当然，目前也支持动态赋值，但我还是推荐直接创建好 AyuItem ，方便管理：

.. warning::

   - 不允许 AyuItem 中字段值的类型（str 和 DataItem）混用，这里只是用于示例展示。
   - 在使用 AyuItem 时，其中各字段值（除了 ``_update_rule``，``_update_keys`` \
     ``_conflict_cols``）的类型都要统一，比如要么都使用 str 类型，要么都使用 ``DataItem`` 类型。

.. code-block:: python

   def parse(self, response):
       mdi = AyuItem(_table="table0")
       mdi.add_field("add_field1", "value1")
       mdi.add_field("add_field2", DataItem(key_value="value2"))
       mdi.add_field("add_field3", DataItem(key_value="value3", notes="add_field3值"))
       # _table 修改可通过以下方式，同样不推荐使用
       mdi["_table"] = "table1"

另外，本库的 item 提供类型转换，以方便后续的各种使用场景：

.. code-block:: python

   # 将本库 AyuItem 转为 dict 的方法
   item_dict = mdi.asdict()
   # 将本库 AyuItem 转为 scrapy Item 的方法
   item = mdi.asitem()

AyuItem 使用详解
==================

详细介绍 AyuItem 支持的使用方法：

创建 AyuItem 实例：

.. code-block:: python

   item = AyuItem(_table="ta")

获取字段：

.. code:: bash

   >>> item["_table"]
   'ta'

.. note::

   虽然也可以通过 ``item._table`` 的形式获取值，但是不建议这样，显得不明了，还是推荐使用 ``item["_table"]`` \
   的方式保持风格统一。

添加 / 修改字段（不存在则创建，存在则修改）：

.. code:: bash

   >>> item["_table"] = "tab"
   >>> item["title"] = "tit"
   >>>
   >>> # 也可通过 add_field 添加字段，但不能重复添加相同字段
   >>> item.add_field("num", 10)
   >>>
   >>> [ item["_table"], item["title"], item["num"] ]
   ['tab', 'tit', 10]

类型转换：

.. code:: bash

   >>> # 内置转为 dict 和 scrapy Item 的方法
   >>>
   >>> item.asdict()
   {'title': 'tit', '_table': 'tab', 'num': 10}
   >>>
   >>> type(item.asitem())
   <class 'ayugespidertools.items.ScrapyItem'>

删除字段：

.. code:: bash

   >>> # 删除字段：
   >>> item.pop("num")
   10
   >>> del item["title"]
   >>> item
   {'_table': 'tab'}

使用示例
==========

只需要在 ``yield item`` 时，按需提前导入 AyuItem，将所有的存储字段和场景补充字段全部添加完整即可。

AyuItem 在 spider 中常用的基础使用方法示例，以本库模板中的 ``basic.tmpl`` 为例来作解释：

.. code-block:: python

   from __future__ import annotations

   from typing import TYPE_CHECKING, Any

   from ayugespidertools.items import AyuItem
   from ayugespidertools.spiders import AyuSpider
   from scrapy.http import Request

   if TYPE_CHECKING:
       from collections.abc import AsyncIterator

       from aiomysql import Pool
       from scrapy.http import Response


   class DemoOneSpider(AyuSpider):
       name = "demo_one"
       allowed_domains = ["readthedocs.io"]
       start_urls = ["http://readthedocs.io/"]
       custom_settings = {
           "ITEM_PIPELINES": {
               # 激活此项则数据会存储至 Mysql
               "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
               # 激活此项则数据会存储至 MongoDB
               "ayugespidertools.pipelines.AyuFtyMongoPipeline": 301,
           },
       }

       async def start(self) -> AsyncIterator[Any]:
           yield Request(
               url="https://ayugespidertools.readthedocs.io/en/latest/",
               callback=self.parse_first,
           )

       def parse_first(self, response: Response) -> Any:
           _save_table = "_octree_info"
           # 你可以自定义解析规则，使用 lxml 还是 response.css response.xpath 等等都可以。
           li_list = response.xpath('//div[@aria-label="Navigation menu"]/ul/li')
           for curr_li in li_list:
               octree_text = curr_li.xpath("a/text()").get()
               octree_href = curr_li.xpath("a/@href").get()

               # 可使用 ayugespidertools.utils.database 来入库前去重查询；
               # 或使用 AyuItem 内置的去重更新功能；
               # 具体使用方法和更多示例，请查看:
               # https://ayugespidertools.readthedocs.io/en/latest/topics/deduplicate.html
               octree_item = AyuItem(
                   octree_text=octree_text,
                   octree_href=octree_href,
                   _table=_save_table,
                   # 这里的更新新增逻辑会在各自的 pipeline 中生效且互不影响，当然你也可以一同设置 postgresql,
                   # oracle 的 pipeline，它们会互不影响且一同生效。
                   _update_rule={"octree_text": octree_text},
                   _update_keys={"octree_href"},
               )
               # 日志使用 scrapy 的 self.logger 或本库的 self.slog
               self.slog.info(f"octree_item: {octree_item}")


由上可知，本库中的 Item 使用方法还是很方便的。

**对以上 Item 相关信息解释：**

- 先导入所需 Item: ``AyuItem``
- 构建对应场景的 ``Item``
  - 若需要使用 AyuItem 内置的去重更新功能，需要自定义 AyuItem 中的内置参数
  - 若只想使用普通存储场景，自己有另外的去重更新方法，那么就不需要设置 AyuItem 中的内置参数

- 最后 ``yield`` 对应 ``item`` 即可

补充：其中 AyuItem 也可以改成 DataItem 的赋值方式，那么 mysql 场景下在表字段不存在时会添加字段注释，\
mongodb 则没有影响。推荐直接赋值的方式，更明了。

.. _topics-items-yield-item:

yield item
==========

本库 item 也是支持直接 ``yield dict`` 和 scrapy 的 item 格式，但还是推荐使用 AyuItem 的形式，比较\
方便且有不错的字段提示功能。

这里介绍下 item 字段及其注释：

.. csv-table::
    :header: "item 字段", "类型", "注释"
    :widths: 10, 15, 30

    "自定义字段", "DataItem，Any", "item 所有需要存储的字段，若有多个，请按规则自定义添加即可。"
    "_table", "DataItem, str", "存储至数据表或集合的名称。"
    "_update_rule", "dict", "去重更新的匹配规则。"
    "_update_keys", "set", "满足去重更新的匹配规则时，需要更新的字段。"
    "_conflict_cols", "set", "使用内置去重规则时，postgresql 和 oracle 场景需要设置的唯一索引约束参数。"
    "_mongo_update_rule", "dict", "旧参数，已用 _update_rule 代替，并在3.14删除。"
    "_mongo_update_keys", "dict", "无效的兼容参数，已用 _update_keys 代替，并在3.14删除。"

.. note::

   这里的 ``自定义字段`` 就是指用户可自定义赋值字段的部分，通过 ``AyuItem(key=value)`` 的形式直接动\
   态赋值，即可自定义 ``key`` 的部分。

一些规则：

.. csv-table::
    :header: "item 字段规则", "类型", "默认值", "使用场景"
    :widths: 45, 15, 15, 20

    "后缀包含 ``_file_url`` 值", "str, DataItem", "不可配置",  "下载文件到本地"
    "后缀包含 ``upload_fields_suffix`` 配置项", "str", "_file_url，可自定义", "上传资源到 oss"
    "前缀包含 ``oss_fields_prefix`` 配置项", "str", "_，可自定义", "上传资源到 oss"


.. note::

   - 在下载文件到本地的场景中，会把后缀包含 ``_file_url`` 的字段对应的资源文件下载到本地，生成的对应新\
     字段会在原字段添加 ``_local`` 后缀来存放对应文件的指向，具体请查看 demo_file 中的示例；
   - 在上传资源文件到 oss 的场景中，需要查看 .conf 中的 ``[oss:ali]`` 的配置项，会将后缀包含 \
     ``upload_fields_suffix (默认参数值为 _file_url)`` 的字段对应的资源文件上传到 oss，生成的对应\
     新字段会在原字段添加 ``oss_fields_prefix (默认参数值为 _)`` 前缀来存放对应文件的指向。其中 \
     upload_fields_suffix 和 oss_fields_prefix 的值可自定义，具体请查看 demo_oss 及 demo_oss_super \
     中的示例。

自定义 Item 字段和实现 Item Loaders
====================================

具体请在下一章浏览。
