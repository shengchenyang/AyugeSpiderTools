.. _diy-mytemplate:

==============================
How-To-Build-Your-Own-Template
==============================

前言
======

在开发爬虫项目时，需要设置各种辅助开发工具的配置内容，比如一些代码类型检查，代码风格整理和一些常用操作等。

就比如 `DemoSpider`_ 中的项目结构，会大大提升团队中的开发体验。

而且，各个项目中的这些配置也都大致一样，那么就可以通过 cookiecutter 来将一些变动的参数和常用的选项提取\
出来整理成一个工程项目模版以供团队使用。

那如何快速创建类似 `DemoSpider`_ 的 Scrapy 工程项目结构呢？

构建方法
==========

   推荐查看 cookiecutter 官方文档，来自定义团队专属的项目模版。

这里提供一个 `LazyScraper`_ 的 cookiecutter 示例，使用方法如下：

.. code:: bash

   # 需要提前安装好 cookiecutter
   pip install cookiecutter

   # 然后根据 repo 模版生成项目
   cookiecutter https://github.com/shengchenyang/LazyScraper.git

补充
======

示例风格并非完全符合每个人的喜好，所以可参考着修改和完善。

.. _DemoSpider: https://github.com/shengchenyang/DemoSpider
.. _LazyScraper: https://github.com/shengchenyang/LazyScraper
