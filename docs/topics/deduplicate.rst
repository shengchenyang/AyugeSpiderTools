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
给数据库字段添加唯一索引，忽略重复插入的错误：

现在可以很方便地通过 AyuItem 中的内置参数结合 mysql，mongodb，postgresql 和 oracledb 的唯一索引即可\
达到入库时自动判断数据是否已存在，不存在就新增插入，存在时也可自定更新哪些字段或忽略它。而且是通过对应数据库\
的一条语句实现，减少像之前那样的先 select 再判断 insert， update 或忽略跳过它而造成的 io 延迟。比如：\
mysql 通过 INSERT INTO ... ON DUPLICATE KEY UPDATE 实现，mongodb 通过 $set 和 $setOnInsert \
实现，postgresql 是通过 INSERT INTO ... ON CONFLICT 实现，oracledb 是通过 MERGE INTO 实现。

.. note::

   在 AyugeSpiderTools 3.13.0 版本中内置了更简洁的去重及更新功能，可以通过设置 AyuItem 即可轻松达到\
   之前先 select 然后再决定 insert 还是 update 或什么也不做的复杂操作，且此方式实现方式更简洁且高效。\
   具体的使用场景和 mongodb，postgresql 和 oracle 数据的示例请在 DemoSpider 中查看。

Mysql
-----

对 mysql 的存储场景进行介绍：

.. note::

   - 使用 AyuItem 内置的 mysql 更新规则时，需要在 .conf 配置中设置   为 True 才能激活更\
     新功能；
   - 再结合 .conf 中设置 insert_ignore 为 True，且不设置 _update_keys 参数时即可做到忽略更新内容，\
     达到只新增不更新已存在内容。这个请按需使用。
   - 当然，你也可以选择保持默认关闭 odku_enable 和关闭 insert_ignore 的配置，不使用 AyuItem 中的\
     内置更新去重功能，使用自己的去重方式来实现。

.. code-block:: python

   from ayugespidertools.items import AyuItem

   octree_item = AyuItem(
       octree_text=octree_text,
       octree_href=octree_href,
       _table=_save_table,
       # 更新逻辑，如果 octree_text 已存在则更新或忽略，不存在会执行插入(需配合唯一索引使用)。
       _update_rule={"octree_text": octree_text},
       # 以 _update_rule 查询条件判断已存在时候，要更新哪些字段。_update_keys 不设置则还是
       # 走新增(注意：在设置了唯一索引时，推荐设置 _update_keys 参数或 insert_ignore 配置
       # 为 true，具体使用方式请按照自己喜欢的来。)
       # 比如此示例，需要在 mysql _table 表设置 octree_text 为唯一索引，插入相同唯一索引
       # 对应的数据会自动触发更新 _update_keys 中的字段，否则就正常新增数据。若你不设置唯一
       # 索引，则会永远执行新增插入。
       # 当然，如果设置了唯一索引且遇到了相同数据，但是并不想走更新逻辑，而是忽略它，那么不设
       # 置 _update_keys 并结合 insert_ignore 即可。
       _update_keys={"octree_href"},
   )
   yield octree_item

MongoDB
-------

对 mongodb 的存储场景进行介绍：

.. warning::

   - 在 ayugespidertools 3.13.0 之前，mongodb 存储场景是通过 _mongo_update_rule 来确定更新规则，\
     如果匹配就会更新 AyuItem 中所有字段。规则有点过于粗暴简陋了。
   - 目前规则中，更新规则字段改为统一的 _update_rule，如果数据已存在，则会更新 _update_keys 中的字段；\
     如果已匹配数据但是没有设置 _update_keys 则并不会更新任何字段；虽然新版本依然支持 _mongo_update_rule \
     和 _mongo_update_keys 字段，但是推荐使用统一内置参数 _update_rule 和 _update_keys，后续会删除\
     _mongo_x 的字段。

.. code-block:: python

   from ayugespidertools.items import AyuItem

   octree_item = AyuItem(
       octree_text=octree_text,
       octree_href=octree_href,
       # 更新规则，如果匹配 _update_rule 则会尝试更新已存在数据的 _update_keys 中的字段。
       _update_rule={"octree_text": octree_text},
       # _update_rule 匹配时自定义更新的字段，支持设置多个，比如 {"octree_href", "new_field"}
       # 如果没有设置则不会更新任何字段。
       _update_keys={"octree_href"},
       _table="demo_two",
   )

   self.slog.info(f"octree_item: {octree_item}")
   yield octree_item

PostgreSQL
----------

对 PostgreSQL 的存储场景进行介绍：

.. note::

   postgresql 的使用和上面 mysql 和 mongodb 的一样，主要是多了一个 _conflict_cols 参数用于指定数\
   据表中的唯一索引约束字段(在设置了唯一索引时，当然也非常推荐结合唯一索引使用)；为什么不使用 merge into \
   接口就可以不用多一个自定义 _conflict_cols 字段了，不是更方便简约吗？是因为它只在 postgresql 15 版本\
   及以上才支持，为了兼容性考虑。


.. code-block:: python

   from ayugespidertools.items import AyuItem

   octree_item = AyuItem(
       octree_text=octree_text,
       octree_href=octree_href,
       start_index=index,
       _table=_save_table,
       _update_rule={"octree_text": octree_text},
       _update_keys={"octree_href"},
       _conflict_cols={"octree_text"},
   )
   self.slog.info(f"octree_item: {octree_item}")
   yield octree_item

Oracle
------

对 Oracle 的存储场景进行介绍：

.. note::

   oracle 的使用和上面 postgresql 的一致，这里就不再多余介绍了。


.. code-block:: python

   from ayugespidertools.items import AyuItem

   octree_item = AyuItem(
       octree_text=octree_text,
       octree_href=octree_href,
       start_index=index,
       _table=_save_table,
       _update_rule={"octree_text": octree_text},
       _update_keys={"octree_href"},
       _conflict_cols={"octree_text"},
   )
   self.slog.info(f"octree_item: {octree_item}")
   yield octree_item

Database
========

一种数据去重的方式是在 ``yield item`` 的 ``spider`` 中根据数据库查询来查看是否需要入库。这里不是使用\
内置的更新功能(AyuItem 中自定义 _update_rule 和 _update_keys 的方式)，这里是提供一个数据库链接接口，\
会更加的灵活，适合更复杂、更自定义的查询场景。

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

MongoDB 场景下除了使用 AyuItem 的方式，也可以使用自定义的方式，推荐 asyncio 的方式。

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
       pool = await PostgreSQLAsyncPortal(db_conf=postgres_conf).connect()

       async with pool.acquire() as conn:
           await conn.fetchrow("SELECT 42;")
       await pool.close()

.. warning::

   - 在 ayugespidertool 3.12.x 旧版本中的 PostgreSQL 入库查询使用方式如下，已经删除此方式，使用较复杂。

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

Oracle 场景下的 asyncio 的数据库链接操作示例:

.. code-block:: python

   from ayugespidertools.utils.database import OracleAsyncPortal


   async def test_example():
       _sql = 'SELECT * from "_article_info_list"'
       pool = OracleAsyncPortal(db_conf=oracle_conf).connect()
       async with pool.acquire() as conn:
           with conn.cursor() as cursor:
               await cursor.execute(_sql)
               exists = await cursor.fetchone()
       await conn.close()

       # 但是更推荐直接使用 conn 操作即可，更简洁，可自行挑选喜欢的方式
       async with pool.acquire() as conn:
           exists = await connection.fetchone(_sql)
       await conn.close()

当然，也可以使用普通的方式来查询：

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
