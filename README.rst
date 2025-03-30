.. image:: https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/master/artwork/ayugespidertools-logo.png
   :target: https://ayugespidertools.readthedocs.io/en/latest/
   :alt: ayugespidertools-logo

========================
AyugeSpiderTools 介绍
========================

.. image:: https://img.shields.io/github/license/shengchenyang/AyugeSpiderTools
   :target: https://img.shields.io/github/license/shengchenyang/AyugeSpiderTools
   :alt: license

.. image:: https://img.shields.io/badge/python-3.9%2B-blue
   :target: https://pypi.org/pypi/Scrapy
   :alt: python support

.. image:: https://img.shields.io/readthedocs/ayugespidertools
   :target: https://ayugespidertools.readthedocs.io/en/latest/
   :alt: Read the Docs

.. image:: https://img.shields.io/github/downloads/shengchenyang/AyugeSpiderTools/total?label=releases%20downloads
   :target: https://github.com/shengchenyang/AyugeSpiderTools/releases
   :alt: GitHub all releases

.. image:: https://img.shields.io/pypi/dm/AyugeSpiderTools?label=pypi%20downloads
   :target: https://pypistats.org/packages/ayugespidertools
   :alt: PyPI - Downloads

.. image:: https://codecov.io/gh/shengchenyang/AyugeSpiderTools/graph/badge.svg?token=1QLOEW2NTI
   :target: https://app.codecov.io/gh/shengchenyang/AyugeSpiderTools
   :alt: codecov

**简体中文** | English_

概述
=======

   一句话介绍：用于扩展 Scrapy 功能来解放双手。

在使用 Scrapy 开发爬虫时，免不了会重复地编写 settings，items，middlewares，pipelines 和一些通用方\
法，但各项目中的这些内容都大致相同，那为何不把它们统一整理在一起呢？我也想扩展一些功能，比如当 spider 中\
添加字段后，不用再修改对应的 item 和 pipeline 甚至不用手动修改 Mysql 和 PostgreSQL 的表结构。

项目的主旨是让开发者只需专注于 spider 脚本的编写，减少开发和维护流程。理想状态下，只需关注 spider 中字\
段的解析规则和 VIT 下的 .conf 配置即可，**脱离无意义的重复操作**。

以 Mysql 存储场景举例：可以自动创建相关数据库，数据表，字段注释，自动添加 spider 中新添加的字段，和自动\
修复常见（字段编码，Data too long，存储字段不存在等）的存储问题。

安装
=======

   可以直接输入以下命令：

.. code:: bash

   pip install ayugespidertools

-------------------------------

   可选安装1，安装数据库相关的所有依赖：

.. code:: bash

   pip install ayugespidertools[database]

-----------------------------------------

   可选安装2，通过以下命令安装所有依赖：

.. code:: bash

   pip install ayugespidertools[all]

注：详细的安装介绍请查看 `安装指南`_。

用法
=======

   开发人员只需根据命令生成示例模板，再配置相关设置即可。

使用方法示例 GIF 如下：

.. image:: https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/master/examples/ayugespidertools-use.gif
   :alt: ayugespidertools-use.gif

对以上 GIF 中的步骤进行解释：
::

   # 查看库版本
   ayuge version

   # 创建项目
   ayuge startproject <project_name>

   # 进入项目根目录
   cd <project_name>

   # 替换(覆盖)为真实的配置 .conf 文件：
   # 这里是为了演示方便，正常情况是直接在 VIT 中的 .conf 文件填上你需要的配置即可
   cp /root/mytemp/.conf DemoSpider/VIT/.conf

   # 生成爬虫脚本
   ayuge genspider <spider_name> <example.com>

   # 运行脚本
   scrapy crawl <spider_name>
   # 注：也可以使用 ayuge crawl <spider_name>

具体的场景案例请在 `DemoSpider`_ 项目中查看，也可以在 `readthedocs`_ 文档中查看教程。目前已适配以下场景：
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

   - 7).demo_seven: 使用 requests 来请求的场景(已删除，更推荐 aiohttp 方式)
   + 8).demo_eight: 同时存入 Mysql 和 MongoDB 的场景
   + 9).demo_aiohttp_example: 使用 aiohttp 来请求的场景
   + 10).demo_aiohttp_test: scrapy aiohttp 在具体项目中的使用方法示例

   + 11).demo_proxy_one: 快代理动态隧道代理示例
   + 12).demo_proxy_two: 测试快代理独享代理
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

超级棒的示例
==============

简单、快速、优雅地实现分布式开发，部署及运行的示例：demo_s，具体介绍请在 `DemoSpider`_ 项目中查看，运\
行示例图为：

.. image:: https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/master/examples/ayugespidertools-async-demo.png
   :alt: async-demo

跑通测试
==========

前提：需要在 tests 的 VIT 目录下创建 .conf 文件，已给出示例文件，请填写测试所需内容，然后：

- 可以直接使用 tox 来运行测试。
- 本库以 `poetry`_ 开发，那么直接新环境下运行 poetry install 后，手动运行目标测试或 pytest 命令来测\
  试等皆可。
- 也可以使用 make 工具，make start 然后 make test 即可。

你可能在意的事
===============

1. 若你觉得某些场景下的功能实现不太符合你的预期，想要修改或添加自定义功能，比如移除对你无用模块、修改库名\
   等，你可以自行修改后 build。

2. 本库主推 scrapy 扩展功能，在使用本库时，不会影响你 scrapy 项目及其它组件。

   也就是说，可使用本库开发原生的 scrapy，也可用 scrapy 的风格来开发，但还是推荐使用 `DemoSpider`_ \
   示例中的风格开发。不会对开发者造成过多的迁移成本。

3. item 中 (媒体)资源字段的存储需求较复杂？比如上传到 oss 功能需要更细分的需求，或者有其它更多类型的对\
   象云存储的需要，我该怎么方便地实现？

   1. 如果你比较了解本项目和 poetry 打包构建的流程，那么推荐你按照项目示例风格将需要功能添加后自行打包并\
      安装，比较方便后续使用；
   2. 因为本身就是 scrapy 项目，所以更推荐使用普通存储场景结合自己编写的 scrapy pipeline 来对 item \
      中的资源上传字段进行个性化处理，达到即保留了此库的通用和便捷，也实现了灵活性。

4. 代码测试覆盖率有点低，考虑增加吗？

   不考虑，场景所依赖服务太多，且云服务等其它因素导致个人维护成本过高，但不必担心，我会和本地服务的自动化\
   测试结合使用。

构建你的专属库
===============

   具体内容请以 `poetry`_ 官方文档为准。

据 `你可能在意的事`_ 可知，你可以 clone 源码后，修改任意方法（比如你的项目场景下可能需要其它的日志配置默\
认值，或添加其它的项目结构模板等），修改完成后 poetry build 或 make build 即可打包使用。

比如你可能需要更新依赖库中 kafka-python 为新版本 x.x.x，那只需 poetry install 安装现有依赖后，再\
poetry add kafka-python==x.x.x 安装目标版本（尽量不要使用 poetry update kafka-python），确定测\
试正常了即可 poetry build 打包使用。

   其它自定义 scrapy 项目的方式

也可以通过 cookiecutter 对项目个性化定制，可参考 `LazyScraper`_ 项目。

**希望此项目能在你遇到扩展 scrapy 功能的场景时对你有所指引。**

功能
=======

- [✓] scrapy 的扩展功能场景

  - [✓] scrapy 脚本运行信息统计和项目依赖表采集量统计，可用于日志记录和预警
  - [✓] 自定义模板，在 ayuge startproject <projname> 和 ayuge genspider <spidername> 时生成适\
    合本库的模板文件
  - [✓] 从远程应用管理服务中获取项目配置

    - [✓] 从 consul 获取项目配置
    - [✓] 从 nacos 获取项目配置（注意：优先级小于 consul）
  - [✓] 代理中间件（独享代理、动态隧道代理）
  - [✓] 随机请求头 UA 中间件，根据 fake_useragent 中的权重来随机
  - [✓] 使用以下工具来替换 scrapy 的 Request 来发送请求

    - [✓] requests: 这个不推荐使用，requests 同步库会降低 scrapy 运行效率\
      （已移除此功能，更推荐 aiohttp 的方式）
    - [✓] aiohttp: 集成将 scrapy Request 替换为 aiohttp 的协程方式
  - [✓] Mysql 存储的场景下适配

    - [✓] 自动创建 Mysql 用户场景下需要的数据库和数据表及字段格式，还有字段注释
  - [✓] MongoDB 存储场景适配
  - [✓] PostgreSQL 存储场景适配
  - [✓] ElasticSearch 存储场景适配
  - [✓] Oracle 存储场景适配
  - [✓] oss 上传场景适配
  - [✓] asyncio 语法支持与 async 第三方库支持示例

    - [✓] spider 中使用 asyncio 的 aiohttp 示例
    - [✓] pipeline 中使用 asyncio 的 aioMysql 示例
  - [✓] 集成 Kafka，RabbitMQ 等数据推送功能
- [✓] 常用开发场景

  - [✓] sql 语句拼接，只用于简单场景。
  - [✓] 数据格式化处理，比如：去除网页标签，去除无效空格等
  - [✓] 字体反爬还原方法

    - [✓] 基于 ttf，woff 之类的字体文件映射，或结合 css 等实现

      - [✓] 可以直接在字体文件 xml 中找到映射关系的：使用 `fontforge`_ 工具导出映射即可。
      - [✓] 无法找到映射关系的，则一般使用 ocr 识别（准确率非百分百），通过 fontforge 导出每个映射的\
        png，后再通过各种方式识别。
    - [✓] 字体反爬部分功能迁移到 FontMapster 项目中。
  - [✓] html 数据处理，去除标签，不可见字符，特殊字符改成正常显示等
  - [✓] 添加常用的图片验证码中的处理方法

    - [✓] 滑块缺口距离的识别方法（多种实现方式）
    - [✓] 根据滑块距离生成轨迹数组的方法
    - [✓] 识别点选验证码位置及点击顺序
    - [✓] 图片乱序混淆的还原方法示例

注意：功能演示我将放入 `readthedocs`_ 文档中，以防此部分内容过多。

感谢
=======

- `scrapy`_

赞助
=======

如果此项目对你有所帮助，可以选择打赏作者。

.. image:: https://github.com/shengchenyang/AyugeSpiderTools/raw/master/artwork/ayugespidertools-donating.jpg
   :alt: 微信赞赏码
   :width: 280

.. _English: https://github.com/shengchenyang/AyugeSpiderTools/blob/master/README_en.rst
.. _安装指南: https://ayugespidertools.readthedocs.io/en/latest/intro/install.html
.. _DemoSpider: https://github.com/shengchenyang/DemoSpider
.. _readthedocs: https://ayugespidertools.readthedocs.io/en/latest/
.. _poetry: https://python-poetry.org/docs/
.. _LazyScraper: https://github.com/shengchenyang/LazyScraper
.. _fontforge: https://github.com/fontforge/fontforge/releases
.. _scrapy: https://github.com/scrapy/scrapy
