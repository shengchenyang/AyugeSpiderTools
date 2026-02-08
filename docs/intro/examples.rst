.. _intro-examples:

======
例子
======

本教程将引导您完成这些任务：

- 快速熟悉 ayugespidertools 库的使用方法和支持场景
- 编写爬虫来抓取站点并提取数据

1. 快速开始
=============

   你可以使用以下两种方式来快速开始：

1.1. 方式一：ayugespidertools
---------------------------------

通过跑通本库 Github 中的 GIF 示例，具体请点击跳转至 `AyugeSpiderTools`_ 查看。若不是很熟悉 Scrapy\
库，可选择先查看本文档中的示例教程。

1.2. 方式二：DemoSpider
--------------------------

另一种较方便的方式是：通过演示项目 `DemoSpider`_ 来快速复现某些场景及功能。

本库 `ayugespidertools github README.md`_ 中所有功能，都可以在 `DemoSpider`_ 中找到示例。

您可以在项目的自述文件中找到有关它的更多信息。

2. 应用场景介绍
================

根据 `DemoSpider`_ 中的各个 spider 对一些应用场景进行简要的补充介绍，总体的介绍为：
::

   + 0).以下场景全支持从 nacos 或 consul 中获取配置，不一一举例。

   # 数据存入 Mysql 的场景：
   + 1).demo_one: 从 .conf 中获取 mysql 配置
   + 3).demo_three: 从 consul 中获取 mysql 配置
   + 21).demo_mysql_nacos: 从 nacos 中获取 mysql 配置
   + 5).demo_five: Twisted 异步存储示例
   + 24).demo_aiomysql: 结合 aiomysql 实现的 asyncio 异步存储示例
   + 13).demo_AyuTurboMysqlPipeline: mysql 同步连接池的示例

   # 数据存入 MongoDB 的场景：
   + 2).demo_two: 从 .conf 中获取 mongodb 配置
   + 4).demo_four: 从 consul 中获取 mongodb 配置
   + 6).demo_six: Twisted 异步存储示例
   + 17).demo_mongo_async: 结合 motor 实现的 asyncio 异步存储示例

   # 数据存入 PostgreSQL 的场景(需要安装 ayugespidertools[database])
   + 22).demo_nine: 从 .conf 中获取 postgresql 配置
   + 23).demo_ten: Twisted 异步存储示例
   + 27).demo_eleven: asyncio 异步存储示例

   # 数据存入 ElasticSearch 的场景(需要安装 ayugespidertools[database])
   + 28).demo_es: 普通同步存储示例
   + 29).demo_es_async: asyncio 异步存储示例

   # 数据存入 Oracle 的场景(需要安装 ayugespidertools[database])
   + 25). demo_oracle: 普通同步存储示例
   + 26). demo_oracle_twisted: Twisted 异步存储示例
   + 36). demo_oracle_async: asyncio 异步存储示例

   - 7).demo_seven: 使用 requests 来请求的场景(已删除，更推荐 aiohttp 方式)
   + 8).demo_eight: 同时存入 Mysql 和 MongoDB 的场景
   + 9).demo_aiohttp_example: 使用 aiohttp 来请求的场景
   + 10).demo_aiohttp_test: scrapy aiohttp 在具体项目中的使用方法示例

   - 11).demo_proxy_one: 快代理动态隧道代理示例(已删除)
   - 12).demo_proxy_two: 测试快代理独享代理(已删除)
   + 37).demo_proxy: 通用代理中间件
   + 14).demo_crawl: 支持 scrapy CrawlSpider 的示例

   # 本库中给出支持 Item Loaders 特性的示例
   + 15).demo_item_loader: 本库中使用 Item Loaders 的示例
   - 16).demo_item_loader_two: 已删除，可查看 demo_item_loader，可方便的使用 Item Loaders 了

   + 18).demo_mq: 数据存入 rabbitmq 的模板示例
   + 35).demo_mq_async: 数据存入 rabbitmq 的异步模板示例
   + 19).demo_kafka: 数据存入 kafka 的模板示例
   + 20).demo_file: 使用本库 pipeline 下载图片等文件到本地的示例
   + 30).demo_file_sec: 自行实现的图片下载示例
   + 31).demo_oss: 使用本库 pipeline 上传到 oss 的示例
   + 32).demo_oss_sec: 自行实现的 oss 上传示例
   + 33).demo_oss_super: MongoDB 存储场景 oss 上传字段支持列表类型
   + 34).demo_conf: 支持从 .conf 中获取自定义配置

基本查看以上 spider 即可了解使用方法，但有些示例还是不够详细，对以上内容进行补充。

- 以上场景有需要 consul 或 nacos 上的相关配置的示例，与 .conf 中的配置内容一致，以下为 json\
  格式配置的示例：

.. code:: json

   {
       "mysql":{
           "host":"***",
           "port":3306,
           "user":"***",
           "password":"***",
           "database":"***",
           "charset":"选填：默认 utf8mb4"
       },
       "mongodb":{
           "host":"***",
           "port":27017,
           "user":"***",
           "password":"***",
           "database":"***",
           "authsource":"***",
           "authMechanism":"选填：默认 SCRAM-SHA-1"
       },
       "postgresql": {
           "host":"***",
           "port":5432,
           "user":"***",
           "password":"***",
           "database":"***",
           "charset":"选填：默认 UTF8"
       },
       "mq":{
           "host":"***",
           "port":5672,
           "username":"***",
           "password":"***",
           "virtualhost":"***",
           "queue":"***",
           "exchange":"***",
           "routing_key":"***"
       },
       "kafka":{
           "bootstrap_servers":"127.0.0.1:9092 #若多个用逗号分隔",
           "topic":"***",
           "key":"***"
       },
       "proxy":{
           "proxy":"http://user:password@host:port"
       }
   }

.. _AyugeSpiderTools: https://github.com/shengchenyang/AyugeSpiderTools
.. _DemoSpider: https://github.com/shengchenyang/DemoSpider
.. _ayugespidertools github README.md: https://github.com/shengchenyang/AyugeSpiderTools#readme
