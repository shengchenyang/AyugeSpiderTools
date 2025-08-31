.. _topics-pipelines:

=========
pipelines
=========

介绍本库中自带的常用 ``pipelines`` 管道。

需要使用本库中的 pipelines 的模板，需要在 spider 中修改如下：

.. code-block:: python

   from ayugespidertools.items import AyuItem
   from ayugespidertools.spiders import AyuSpider


   class DemoOneSpider(AyuSpider):  # 第一处
       name = "demo_es"
       custom_settings = {
           "ITEM_PIPELINES": {
               # 比如使用 Mysql 存储场景，激活此项则数据会存储至 Mysql
               "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,  # 第二处
           },
       }
       ...

       def parse(self, response):
           ...
           yield AyuItem(...)  # 第三处

由上可知，使用还是比较简单的，记得其中三处的内容即可。以下内容不再对写法进行描述，都是相同的。

1. Mysql 存储
================

1.1. AyuFtyMysqlPipeline
-----------------------------

1.1.1. 介绍
^^^^^^^^^^^^^^^^

``AyuFtyMysqlPipeline`` 为 mysql 同步存储的普通模式，具有自动创建所需数据库，数据表，自动动态管理 \
table 字段，表注释，也会自动处理常见（字段编码，``Data too long``，存储字段不存在等等）的存储问题。\
属于经典的示例，也是网上教程能搜到最多的存储方式。

1.1.2. 相关示例
^^^^^^^^^^^^^^^^^^^

可在 `DemoSpider`_ 中的 ``demo_one``，``demo_three``，``demo_crawl``，``demo_eight``，\
``demo_file``，``demo_item_loader``，``demo_mysql_nacos`` 中查看具体的代码示例。

1.2. AyuTwistedMysqlPipeline
---------------------------------

1.2.1. 介绍
^^^^^^^^^^^^^^^^

结合 ``twisted``  实现 Mysql 存储场景下的异步操作。同样不用手动创建数据库表及字段。比较推荐此方式方式，\
比较成熟。

1.2.2. 相关示例
^^^^^^^^^^^^^^^^^^^

可在 DemoSpdider 项目中的 ``demo_five`` 中查看。

1.3. AyuAsyncMysqlPipeline
------------------------------

1.3.1. 介绍
^^^^^^^^^^^^^^^^

结合 ``aiomysql`` 实现的 ``async`` 异步存储功能。目前需要手动创建数据库表及字段。

1.3.2. 相关示例
^^^^^^^^^^^^^^^^^^^

可在 DemoSpdider 项目中的 ``demo_aiomysql`` 中查看示例。

2. MongoDB 存储
==================

2.1. AyuFtyMongoPipeline
-----------------------------

``AyuFtyMysqlPipeline`` 为 ``mongodb`` 同步存储的普通模式。

可在 DemoSpider 中的 ``demo_two``，``demo_four``，``demo_eight`` 中查看具体的代码示例。

2.2. AyuTwistedMongoPipeline
---------------------------------

结合 ``twisted``  实现 ``mongodb`` 存储场景下的异步操作。

可在 DemoSpdider 项目中的 ``demo_six`` 中查看示例。

2.3. AyuAsyncMongoPipeline
--------------------------------

结合 ``motor`` 实现的 ``async`` 的异步存储功能。

可在 DemoSpdider 项目中的 ``demo_mongo_async`` 中查看示例。

3. PostgreSql 存储
=====================

就不再分别介绍了，命名规则一致，可通过对应的 ``AyuFtyPostgresPipeline``，``AyuTwistedPostgresPipeline``，\
``AyuAsyncPostgresPipeline``  即可知其具体的场景及功能。其中 asyncio 场景下也暂不支持自动创建库表及字段。

4. Oracle 存储
=================

同样地，具有的 pipelines 有 ``AyuFtyOraclePipeline``， ``AyuTwistedOraclePipeline`` 和 \
``AyuAsyncOraclePipeline``， 但全都没有自动创建库表的功能，因为其相关报错没有其他库那么精准，虽也可\
实现但没有必要，请手动创建所需的库表及字段。

注意：``AyuAsyncOraclePipeline`` 是在 ayugespidertools 3.13.0 版本才添加的功能。

5. ElasticSearch 存储
========================

同样地，具有的 pipelines 有 ``AyuFtyESPipeline`` 和 ``AyuAsyncESPipeline``，没有结合 ``twisted`` \
实现的异步方式。

可在 DemoSpdider 项目中的 ``demo_es`` 和 ``demo_es_async`` 中查看示例。

6. 消息推送服务
=================

6.1. mq
------------

> 此场景下给出的是以 pika 实现的 ``RabbitMQ`` 的示例

对应的 pipelines 名称为 ``AyuMQPipeline``，其中 .conf 中的所需配置如下：

.. code:: ini

   [mq]
   host=***
   port=5672
   username=***
   password=***
   virtualhost=***
   queue=***
   exchange=***
   routing_key=***

   # 一般只需配置以上参数即可，因为会有一些默认值，如果不需更改则不用配置，比如以下为非必须参数及其默认值：
   durable=True
   exclusive=False
   auto_delete=False
   content_type="text/plain"
   delivery_mode=1
   mandatory=True

然后在 spider 中 yield 你所需结构的 item 即可（类型为 ``dict``）。

6.2. kafka
--------------

此场景给出的是以 ``kafka-python`` 实现的 ``kafka`` 推送示例

对应的 pipelines 名称为 ``AyuKafkaPipeline``，其中 .conf 中的所需配置如下：

.. code:: ini

   [kafka]
   bootstrap_servers=127.0.0.1:9092 #若多个用逗号分隔
   topic=***
   key=***

然后在 spider 中 yield 你所需结构的 item 即可（类型为 ``dict``）。

7. 文件下载
==============

需要激活 ``ITEM_PIPELINES`` 对应的配置，然后在项目中配置相关参数。

spider 中的 ``custom_settings`` 所需配置如下：

.. code-block:: python

   "ITEM_PIPELINES": {
       "ayugespidertools.pipelines.FilesDownloadPipeline": 300,
       # 以下 AyuFtyMysqlPipeline 非必须，但只激活 FilesDownloadPipeline 时只会下载文件，但是
       # 并不会将信息与网页中的标题、描述等信息绑定，激活 AyuFtyMysqlPipeline 之类的选项后，可以自行
       # 添加其它可以描述文件的详细字段并存储对应场景的数据库中。
       "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 301,
   }

spider 等其它项目配置中的所需详细设置示例如下：

.. code:: ini

   from pathlib import Path

   custom_settings = {
       "ITEM_PIPELINES": {
           "ayugespidertools.pipelines.FilesDownloadPipeline": 300,
           "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 301,
       },
       # 下载文件保存路径
       "FILES_STORE": Path(__file__).parent.parent / "docs",
   }

具体示例请在 `DemoSpider`_ 项目中的 ``demo_file`` 和 ``demo_file_sec`` 查看。

8. oss 上传
==============

此场景给出的是以 ``oss2`` 实现的 ``oss`` 上传示例

对应的 pipelines 名称为 ``AyuAsyncOssPipeline``，其中 .conf 中的所需配置如下：

具体的配置解释不再介绍了，请在 item 部分查看。

.. code:: ini

   [oss:ali]
   access_key=
   access_secret=
   endpoint=
   bucket=
   doc=
   upload_fields_suffix=_file_url
   oss_fields_prefix=_

.. _DemoSpider: https://github.com/shengchenyang/DemoSpider
.. _oracledb v2.0.0: https://github.com/oracle/python-oracledb/releases/tag/v2.0.0
