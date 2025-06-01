.. _topics-deduplicate:

===========
Deduplicate
===========

在使用 Scrapy 或其它工具开发爬虫时，数据去重一直是必要步骤，选择去重的方式也是各种各样：比如基于内存，基\
于文件，基于 redis，基于入库前 item 唯一字段查询，基于 url 请求指纹等。这里提供一些简单常用的方法，具体\
使用哪种方式请根据应用场景按需选择。

唯一索引 & 项目配置
=====================

一种数据去重的方式是在 ``yield item`` 后 ``pipeline`` 入库时根据库中数据来决定是否新增或更新等，比如\
给数据库字段添加唯一索引，忽略重复插入的错误(MYSQL: INSERT IGNORE)，ON DUPLICATE KEY UPDATE(MYSQL)，\
upsert(MongoDB) 更新当前项等规则来设置数据入库方式。

比如本库在 Mysql 场景下的 .conf odku_enable 配置并结合唯一索引可以达到当数据重复时更新当前项，或者选\
择 insert_ignore 的配置来忽略重复的数据，请按照场景需要自行选择。

本库在 MongoDB 场景下的 AyuItem 中的 _mongo_update_rule 配置，或者再结合唯一索引在 asyncio 场景会\
更优雅且可靠，也是本库最推荐的去重的方式之一。

Database
========

一种数据去重的方式是在 ``yield item`` 的 ``spider`` 中根据数据库查询来查看是否需要入库。其实 MongoDB \
场景下的 AyuItem 中的 _mongo_update_rule 配置和唯一索引方式也是属于这个范畴。只是这里提供一个数据库链\
接接口，会更加的灵活，适合更复杂、更自定义的查询场景。

这里提供的接口是 ``ayugespidertools.utils.database``，里面提供了最常见的数据库链接功能。分别介绍他们：

Mysql
-----

Mysql 场景下除了使用 insert_ignore 或 odku_enable 的配置外，可以使用自定义的方式，推荐使用 asyncio 的方式来查询：

.. code-block:: python

   from ayugespidertools.utils.database import MysqlAsyncPortal


   async def test_example():
       conn = MysqlAsyncPortal(db_conf=mysql_conf)
       pool = await conn.connect()
       async with pool.acquire() as conn:
           async with conn.cursor() as cursor:
               await cursor.execute("SELECT 42;")
       await conn.close()

当然，也可以使用普通的方式来查询：

.. code-block:: python

   from ayugespidertools.utils.database import MysqlPortal


   def test_example():
       conn = MysqlPortal(db_conf=mysql_conf).connect()
       cursor = conn.cursor()
       cursor.execute("SELECT 42;")
       conn.close()

MongoDB
-------

MongoDB 场景下除了使用 AyuItem _mongo_update_rule 的方式，也可以使用自定义的方式，推荐 asyncio 的方式。

.. code-block:: python

   from ayugespidertools.utils.database import MongoDBAsyncPortal


   async def test_example():
       db = MongoDBAsyncPortal(db_conf=mongo_conf).connect()
       res = await db["test_collection"].find_one({"key": "value"}, {"_id": 1})
       db.client.close()

当然，也可以使用普通的方式来查询：

.. code-block:: python

   from ayugespidertools.utils.database import MongoDBPortal


   def test_example():
       db = MongoDBPortal(db_conf=mongo_conf).connect()
       res = db["test_collection"].find_one({"key": "value"}, {"_id": 1})
       db.client.close()

PostgreSQL
----------

PostgreSQL 场景下的 asyncio 的数据库链接操作示例：

.. code-block:: python

   from ayugespidertools.utils.database import PostgreSQLAsyncPortal


   async def test_example():
       conn = PostgreSQLAsyncPortal(db_conf=postgres_conf)
       pool = conn.connect()
       await pool.open()

       async with pool.connection() as conn:
           async with conn.cursor() as cursor:
               await cursor.execute("SELECT 42;")
       await pool.close()

当然，也可以使用普通的方式来查询：

.. code-block:: python

   from ayugespidertools.utils.database import PostgreSQLPortal


   def test_example():
       conn = PostgreSQLPortal(db_conf=postgres_conf).connect()
       cursor = conn.cursor()
       cursor.execute("SELECT 42;")
       conn.close()

Oracle
------

PostgreSQL 场景下的的数据库链接操作示例，这里只提供了普通场景：

.. code-block:: python

   from ayugespidertools.utils.database import OraclePortal


   def test_example():
       conn = OraclePortal(db_conf=oracle_conf).connect()
       cursor = conn.cursor()
       cursor.execute("SELECT 42;")
       conn.close()

Redis
=====

本库给了一个非常简约的根据 redis 查询数据是否已存在的方法，可用于简单场景的判断：

.. code-block:: python

   from ayugespidertools.extras.deduplicate import Deduplicate

   dp = Deduplicate(name="test", redis_url="redis://:password@localhost:6379/0")
   # 查看 key1 是否已存在，如果不存在就自动添加到 redis 中
   res: int = dp.exists("key1")
   # 查看 key2 是否已存在，如果不存在不会自动添加到 redis 中
   res2: int = dp.get("key2")
