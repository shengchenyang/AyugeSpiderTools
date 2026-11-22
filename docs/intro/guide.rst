.. _intro-guide:

AyugeSpiderTools 交互式向导
============================

用 AyugeSpiderTools 开发第一个 Scrapy 项目，快速复现最小示例。

.. _guide-steps:

学习步骤
--------


.. tab-set::
   :sync-group: guide-step

   .. tab-item:: 1. 安装工具
      :class-label: sd-px-2 sd-text-nowrap
      :name: install
      :sync: install

      .. only:: builder_html or builder_dirhtml

         .. raw:: html

            <p><label>第 1 步 / 共 6 步 <progress value="1" max="6"></progress></label></p>

      在 Python 3.11 或更新版本的虚拟环境中安装 AyugeSpiderTools，并检查 CLI 是否可用。

      .. code-block:: bash
         :caption: 终端
         :linenos:

         # 推荐在虚拟环境中安装
         pip install ayugespidertools
         ayuge version

      看到正常输出 AyugeSpiderTools 的版本号后，就可以用 ayuge 命令创建项目。

      .. only:: builder_html or builder_dirhtml

         .. grid:: 2
            :gutter: 2

            .. grid-item::

               ..

            .. grid-item::

               .. button-link:: ?guide-step=project#guide-steps
                  :color: primary

                  下一步 →

   .. tab-item:: 2. 创建项目
      :class-label: sd-px-2 sd-text-nowrap
      :name: project
      :sync: project

      .. only:: builder_html or builder_dirhtml

         .. raw:: html

            <p><label>第 2 步 / 共 6 步 <progress value="2" max="6"></progress></label></p>

      用脚手架创建 ``Guide`` 项目，然后进入包含 ``scrapy.cfg`` 的项目根目录。

      .. code-block:: bash
         :caption: 终端
         :linenos:

         ayuge startproject Guide
         cd Guide

      生成的项目结构如下，除了 VIT 外，其他与 Scrapy 目录及内容一致，目录层级示例如下。

      .. code-block:: text
         :linenos:

         Guide/
         |-- Guide
         |   |-- __init__.py
         |   |-- items.py
         |   |-- middlewares.py
         |   |-- pipelines.py
         |   |-- settings.py
         |   |-- spiders
         |   |   |-- __init__.py
         |   `-- VIT
         |       `-- .conf
         `-- scrapy.cfg

      .. only:: builder_html or builder_dirhtml

         .. grid:: 2
            :gutter: 2

            .. grid-item::

               .. button-link:: ?guide-step=install#guide-steps
                  :color: secondary
                  :outline:

                  ← 上一步

            .. grid-item::

               .. button-link:: ?guide-step=spider#guide-steps
                  :color: primary

                  下一步 →

   .. tab-item:: 3. 生成 Spider
      :class-label: sd-px-2 sd-text-nowrap
      :name: spider
      :sync: spider

      .. only:: builder_html or builder_dirhtml

         .. raw:: html

            <p><label>第 3 步 / 共 6 步 <progress value="3" max="6"></progress></label></p>

      使用 ``genspider`` 命令生成名为 ``demo`` 的 Spider。

      .. code-block:: bash
         :caption: 终端 · 项目根目录
         :linenos:

         # 默认使用 basic 模板来生成脚本
         ayuge genspider demo readthedocs.io

         # 也可以指定其他模板来生成, 比如基于 RabbitMQ 实现的分布式任务分发：
         # (这里只是告知你有这个功能，此向导中不用运行以下部分)
         # ayuge genspider -t task demo readthedocs.io

      生成的文件位于 ``Guide/spiders/demo.py``。下一步来确定 Spider 的复现场景。

      .. only:: builder_html or builder_dirhtml

         .. grid:: 2
            :gutter: 2

            .. grid-item::

               .. button-link:: ?guide-step=project#guide-steps
                  :color: secondary
                  :outline:

                  ← 上一步

            .. grid-item::

               .. button-link:: ?guide-step=scene#guide-steps
                  :color: primary

                  下一步 →

   .. tab-item:: 4. 确认 Spider 场景
      :class-label: sd-px-2 sd-text-nowrap
      :name: scene
      :sync: scene

      .. only:: builder_html or builder_dirhtml

         .. raw:: html

            <p><label>第 4 步 / 共 6 步 <progress value="4" max="6"></progress></label></p>

      编辑 ``Guide/spiders/demo.py``，这里以复现 mongoDB 存储场景为例，在 ``ITEM_PIPELINES`` \
      里只保留 MongoDB Pipeline。下方高亮标出了要删除的三行，注意只修改这一处即可。

      .. code-block:: python
         :caption: Guide/spiders/demo.py
         :linenos:
         :emphasize-lines: 21,23,24

         from __future__ import annotations

         from typing import TYPE_CHECKING, Any

         from ayugespidertools.items import AyuItem
         from ayugespidertools.spiders import AyuSpider
         from scrapy.http import Request

         if TYPE_CHECKING:
             from collections.abc import AsyncIterator

             from scrapy.http.response import Response


         class DemoSpider(AyuSpider):
             name = "demo"
             allowed_domains = ["readthedocs.io"]
             start_urls = ["https://readthedocs.io"]
             custom_settings = {
                 "ITEM_PIPELINES": {
                     "ayugespidertools.pipelines.AyuAsyncMysqlPipeline": 300,
                     "ayugespidertools.pipelines.AyuAsyncMongoPipeline": 301,
                     "ayugespidertools.pipelines.AyuAsyncPostgresPipeline": 302,
                     "ayugespidertools.pipelines.AyuAsyncOraclePipeline": 303,
                 },
             }

             async def start(self) -> AsyncIterator[Any]:
                 yield Request(
                     url="https://ayugespidertools.readthedocs.io/en/latest/",
                     callback=self.parse_first,
                     dont_filter=True,
                 )

             async def parse_first(self, response: Response) -> Any:
                 li_list = response.xpath('//div[@aria-label="Navigation menu"]/ul/li')
                 for curr_li in li_list:
                     octree_text = curr_li.xpath("a/text()").get()
                     octree_href = curr_li.xpath("a/@href").get()

                     # Documentation for AyuItem update support:
                     # https://ayugespidertools.readthedocs.io/en/latest/topics/deduplicate.html
                     yield AyuItem(
                         octree_text=octree_text,
                         octree_href=octree_href,
                         _table="demo_eight",
                         _update_rule={"octree_text": octree_text},
                         _update_keys={"octree_href"},
                     )

      确认 ``AyuAsyncMongoPipeline`` 已启用，然后在下一步填写 MongoDB 的连接信息。

      .. only:: builder_html or builder_dirhtml

         .. grid:: 2
            :gutter: 2

            .. grid-item::

               .. button-link:: ?guide-step=spider#guide-steps
                  :color: secondary
                  :outline:

                  ← 上一步

            .. grid-item::

               .. button-link:: ?guide-step=conf#guide-steps
                  :color: primary

                  下一步 →

   .. tab-item:: 5. 配置 .conf
      :class-label: sd-px-2 sd-text-nowrap
      :name: conf
      :sync: conf

      .. only:: builder_html or builder_dirhtml

         .. raw:: html

            <p><label>第 5 步 / 共 6 步 <progress value="5" max="6"></progress></label></p>

      打开 ``Guide/VIT/.conf``，填入 MongoDB 连接信息。

      .. code-block:: ini
         :caption: Guide/VIT/.conf
         :linenos:
         :emphasize-lines: 2

         [mongodb:uri]
         uri=mongodb://admin:AyugeSpiderTools@127.0.0.1:27017/demo?authSource=admin&authMechanism=SCRAM-SHA-1

      如果已有 MongoDB 实例时，按实际连接信息填写 ``uri``。以下是快速启动以上 mongodb:uri 依赖的 mongoDB 镜像示例：

      .. code-block:: bash
         :caption: 终端 · 可选
         :linenos:

         docker run -d --name mongodb \
           -e MONGO_INITDB_DATABASE=demo \
           -e MONGO_INITDB_ROOT_USERNAME=admin \
           -e MONGO_INITDB_ROOT_PASSWORD=AyugeSpiderTools \
           -p 127.0.0.1:27017:27017 mongo:6.0

      .. only:: builder_html or builder_dirhtml

         .. grid:: 2
            :gutter: 2

            .. grid-item::

               .. button-link:: ?guide-step=scene#guide-steps
                  :color: secondary
                  :outline:

                  ← 上一步

            .. grid-item::

               .. button-link:: ?guide-step=run#guide-steps
                  :color: primary

                  下一步 →

   .. tab-item:: 6. 运行
      :class-label: sd-px-2 sd-text-nowrap
      :name: run
      :sync: run

      .. only:: builder_html or builder_dirhtml

         .. raw:: html

            <p><label>第 6 步 / 共 6 步 <progress value="6" max="6"></progress></label></p>

      在包含 ``scrapy.cfg`` 的项目根目录运行 Spider。

      .. code-block:: bash
         :caption: 终端 · 项目根目录
         :linenos:

         ayuge crawl demo

      项目默认将 error 级别日志保存到 ``Guide/logs/``。运行成功后，检查 MongoDB 的 ``demo`` 数据库中是否出现第四步中的 ``_table`` 对\
      应的集合与采集数据。

      运行不会输出日志，如果在开发中需要调试则需要在 settings.py 中修改即可。

      .. only:: builder_html or builder_dirhtml

         .. grid:: 2
            :gutter: 2

            .. grid-item::

               .. button-link:: ?guide-step=conf#guide-steps
                  :color: secondary
                  :outline:

                  ← 上一步

            .. grid-item::

               .. button-link:: ?guide-step=install#guide-steps
                  :color: primary

                  ↺ 从头开始

更多用法见 :doc:`AyugeSpiderTools 教程 <tutorial>`。
