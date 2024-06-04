.. AyugeSpiderTools documentation master file, created by
   sphinx-quickstart on Thu Feb 16 15:27:14 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


.. _topics-index:

==========================================
AyugeSpiderTools |version| documentation
==========================================


在此之前，我们需要了解 ``Scrapy`` 是一个快速的高级 `网络爬虫`_ 和 `网页抓取`_ 的框架，用于抓取网站并从其网页中提取结构化数据。它可以用于广泛的目\
的，从数据挖掘到监控和自动化测试。

``AyugeSpiderTools`` 是充分发挥 ``Scrapy`` 的模板功能的一个工具库，可以很方便地管理 ``Scrapy`` 项目，比如可以使得我们方便地生成 ``Scrapy`` 项目结构，当使\
用本库内置工具时可以不用每次手动创建 ``items``，``middlewares``，``pipelines``，``settings`` 等，内置了比较通用和常见的 ``middlewares`` 和 ``pipelines``。\
但如果你常用的功能不在此库中，你可以自行添加修改后 ``build`` 成为你专属的工具库。


.. _网络爬虫: https://en.wikipedia.org/wiki/Web_crawler
.. _网页抓取: https://en.wikipedia.org/wiki/Web_scraping

.. _getting-help:

Getting help
==================================

遇到麻烦？请优先尝试使用以下方式提问！

* 请在本库 `ayugespidertools github`_ 上提 ``issues``。
* 除非一些功能性 ``bug``，其它的功能依赖于 ``scrapy``，你或许能在 `scrapy issues`_ 或社区中找到答案。
* 若有其它问题也可尝试 `邮箱`_ 联系。

.. _ayugespidertools github: https://github.com/shengchenyang/AyugeSpiderTools/issues
.. _scrapy issues: https://github.com/scrapy/scrapy/issues
.. _邮箱: ayugesheng@gmail.com


第一步
==================================

.. toctree::
   :caption: 第一步
   :hidden:

   intro/overview
   intro/install
   intro/tutorial
   intro/examples

:doc:`intro/overview`
    了解什么是 AyugeSpiderTools 以及它如何为您提供帮助。

:doc:`intro/install`
    在您的设备上安装 AyugeSpiderTools。

:doc:`intro/tutorial`
    编写您的第一个 AyugeSpiderTools 项目。

:doc:`intro/examples`
    通过一个简单示例来了解一些信息。

基本概念
==================================

.. toctree::
   :caption: 基本概念
   :hidden:

   topics/commands
   topics/items
   topics/loaders
   topics/settings
   topics/configuration

:doc:`topics/commands`
    了解用于管理 ``Scrapy`` 项目的命令行工具。

:doc:`topics/items`
    定义要采集的数据。

:doc:`topics/loaders`
    用提取的数据填充你的 ``item``。

:doc:`topics/settings`
    了解如何配置 ``AyugeSpiderTools`` 并查看所有可用设置。

:doc:`topics/configuration`
    了解如何配置 ``AyugeSpiderTools`` 的 ``.conf`` 内容。

内置服务
==================================

.. toctree::
   :caption: 内置服务
   :hidden:

   topics/logging

:doc:`topics/logging`
    在 ``ayugespidertools`` 上学习如何使用日志。

扩展 scrapy
==================================

.. toctree::
   :caption: 扩展 scrapy
   :hidden:

   topics/downloader-middleware
   topics/pipelines

:doc:`topics/downloader-middleware`
    了解本库中的下载中间件及使用方法。

:doc:`topics/pipelines`
    了解本库中的管道及使用方法。

构建你的专属库
==================================

.. toctree::
   :caption: 构建你的专属库
   :hidden:

   diy/myself
   diy/mytemplate
   additional/contribute

:doc:`diy/myself`
    如何将本库构建成为你的专属库。

:doc:`diy/mytemplate`
    如何快速创建 ``AyugeSpiderTools`` 或 ``Scrapy`` 工程项目结构。

:doc:`additional/contribute`
    贡献指南。

补充说明
==================================

.. toctree::
   :caption: 补充说明
   :hidden:

   additional/news

:doc:`additional/news`
    查看最近的 ``AyugeSpiderTools`` 版本中有哪些变化。
