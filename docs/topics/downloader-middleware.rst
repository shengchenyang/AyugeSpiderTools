.. _topics-downloader-middleware:

=====================
downloader-middleware
=====================

介绍本库中自带的常用 DOWNLOADER_MIDDLEWARES 中间件。若需要使用本库中的配置，需要在 spider 中修改如下，\
此为前提：

.. code-block:: python

   from ayugespidertools.spiders import AyuSpider


   # 当前 spider 要继承 AyuSpider
   class DemoOneSpider(AyuSpider): ...

1. 随机UA
============

使用 fake_useragent 库中的 ua 信息，在每次发送请求时将随机取 ua 信息，将比较常用的 ua 标识的权重设置\
高一点，这里是根据 fake_useragent 库中的打印信息来规划权重的，即类型最多的 ua 其权重也就越高。

1.1. 使用方法
-----------------

只需激活 DOWNLOADER_MIDDLEWARES 对应的配置即可。

.. code-block:: python

   custom_settings = {
       "DOWNLOADER_MIDDLEWARES": {
           # 随机请求头
           "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
       },
   }

.. note::

   若想查看是否正常运行，只需查看其 scrapy 的 debug 日志，或在 spider 中打印 response 信息然后查看\
   其信息即可。

2. 代理
==========

2.1. 中间件代理方式
---------------------

本库给出简单通用的中间件代理示例。

2.1.1. 使用方法
^^^^^^^^^^^^^^^^^^^

激活 DOWNLOADER_MIDDLEWARES 中的动态代理配置。

.. code-block:: python

   custom_settings = {
       "DOWNLOADER_MIDDLEWARES": {
           # 动态隧道代理激活
           "ayugespidertools.middlewares.ProxyDownloaderMiddleware": 125,
       },
   }

需要修改此项目中的 VIT 文件夹下的 .conf 中 [proxy] 的配置信息。

.. code:: ini

   [proxy]
   proxy=http://user:password@host:port

然后即可正常运行。

2.2. 自定义代理中间件
---------------------

2.2.1. 使用方法
^^^^^^^^^^^^^^^^^^^

如果不太喜欢库中通用代理中间件示例，你可以根据 `custom_section`_ 的自定义配置创建对应的自定义代理中间件。\
这里不再举例。

2.3. aiohttp 的代理方式
------------------------

2.3.1. 使用方法
^^^^^^^^^^^^^^^^^^^

除了自带的通用代理中间件、自定义配置解析的代理中间件，你也可以通过使用 aiohttp 发送请求时设置代理参数。\
具体示例请查看 :ref:`downloader-middleware <topics-downloader-middleware-aiohttp>` 的部分文档。

.. _topics-downloader-middleware-aiohttp:

3. 发送请求方式改为 aiohttp
============================

3.1. 使用方法
-----------------

激活 DOWNLOADER_MIDDLEWARES 中的对应配置。

.. code-block:: python

   custom_settings = {
       "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
       "DOWNLOADER_MIDDLEWARES": {
           # 将 scrapy Request 替换为 aiohttp 方式
           "ayugespidertools.middlewares.AiohttpDownloaderMiddleware": 543,
       },
       # aiohttp.TCPConnector 的配置项，非必需项，按需配置
       "AIOHTTP_CONFIG": {
           "sleep": 1,
           # 同时连接的总数
           "limit": 100,
           # 同时连接到一台主机的数量
           "limit_per_host": 0,
           "retry_times": 3,
           "verify_ssl": False,
           "allow_redirects": False,
       },
       # aiohttp 的超时时间也用这个配置
       "DOWNLOAD_TIMEOUT": 25,
   }

.. note::

   - TWISTED_REACTOR 的配置在本库的 settings 中就默认打开的，这里配置是为了演示，不用再次配置的；
   - 这里的 scrapy DOWNLOAD_TIMEOUT 同样也是 aiohttp 请求的超时设置参数；
   - AIOHTTP_CONFIG 为 aiohttp 的全局配置，是构建 aiohttp.ClientSession 的 connector 时所需的\
     参数；

AIOHTTP_CONFIG 可配置的参数如下(其实就是 aiohttp.TCPConnector 中的参数):

.. code-block:: python

   AIOHTTP_CONFIG = {
       # 设置 aiohttp.TCPConnector 中的配置
       "verify_ssl": None,
       "fingerprint": None,
       "use_dns_cache": None,
       "ttl_dns_cache": None,
       "family": None,
       "ssl_context": None,
       "ssl": None,
       "local_addr": None,
       "resolver": None,
       "keepalive_timeout": None,
       "force_close": None,
       "limit": None,
       "limit_per_host": None,
       "enable_cleanup_closed": None,
       "loop": None,
       "timeout_ceil_threshold": None,
       # 设置一些自定义的全局参数
       "sleep": None,
       "retry_times": None,
   }

目前版本简化了 aiohttp 在 yield AiohttpRequest 的操作，也删除了 AiohttpFormRequest 来简化流程，\
示例如下：

.. code-block:: python

   from ayugespidertools.request import AiohttpRequest
   from scrapy.http.request import NO_CALLBACK

   _ar_headers_ck = "headers_ck_key=ck; headers_ck_key2=ck"
   _ar_ck = {"ck_key": "ck"}


   def request_example():
       # 发送 get 请求示例：
       yield AiohttpRequest(
           url="http://httpbin.org/get?get_args=1",
           callback=NO_CALLBACK,
           headers={"Cookie": _ar_headers_ck},
           cookies=_ar_ck,
           cb_kwargs={"request_name": 1},
       )

       # 发送 post 请求示例：
       post_data = {"post_key1": "post_value1", "post_key2": "post_value2"}
       yield AiohttpRequest(
           url="http://httpbin.org/post",
           method="POST",
           callback=NO_CALLBACK,
           headers={"Cookie": _ar_headers_ck},
           data=post_data,
           cookies=_ar_ck,
           cb_kwargs={"request_name": 2},
           dont_filter=True,
       )


   # 其中 AiohttpRequest 中的 params，json，data，proxy，ssl，timeout 等参数可按需求自定义设置。

由于改成通过 yield AiohttpRequest 的统一接口发送请求，且此方法参数与 aiohttp 的请求参数一致，极大地\
减少用户使用成本和避免维护地狱。

.. _custom_section: https://ayugespidertools.readthedocs.io/en/latest/topics/configuration.html#custom-section
