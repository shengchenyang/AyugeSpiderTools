.. _topics-rabbitspider:

============
RabbitSpider
============

本库添加了一个 AyuRabbitMQSpider 来提供依赖 rabbitmq 实现的任务分发功能，可以通过 mq 的任务队列来发\
送任务，可以方便地达到分布式部署，不涉及主从爬虫的概念，直接部署启动你所需要的爬虫数即可。非常适合以 mq 为\
任务队列和推送运行结果，结合不同的 pipeline 或者根据不同的 ayugespidertools.utils.database 中的数\
据库链接实现自定义的存储和推送 mq 结果的公告功能，具体的实现方式请自行选择。

使用方法
=============

这里以 DemoSpider 项目中的 demo_mq_task 为例说明。

1.1. 配置任务 mq 连接信息
---------------------------

需要在 .conf 中的配置文件中配置分发任务的 mq 连接信息，比如这里的 spider 名称为 demo_mq_task：

.. code-block:: ini

   [spider:demo_mq_task]
   name=demo_mq_task
   task_mq=demo_mq_task_mq
   result_mq_queue1=
   result_mq_queue2=
   result_mq_queuen=

   [demo_mq_task_mq]
   virtualhost=ayuge_vh
   queue=ayuge_q
   username=ayuge_u
   password=ayuge_p
   host=127.0.0.1
   port=5672

.. note::

   其中 [spider:<spider_name>]  部分用于声明当前 spider 对应的任务队列名称，然后 [<task_mq>] 就是\
   指此任务队列的具体连接信息，具体的配置参数及解释请在 `custom_section`_ 中的 [mq] 和 [spider:<spider_name>] \
   中查看。

1.2. 运行示例
-----------------

直接运行 demo_mq_task 的示例 spider 即可，具体的运行数可自定义。

1.3. 发送任务
-----------------

你可以通过 DemoSpider 中的 demo_mq 或 demo_mq_async 或自己的脚本来发送采集任务，当任务队列中有数据时\
会自动触发 spider 的采集任务。

.. _custom_section: https://ayugespidertools.readthedocs.io/en/latest/topics/configuration.html#spider-spider-name
