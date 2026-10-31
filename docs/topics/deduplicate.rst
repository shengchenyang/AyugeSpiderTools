.. _topics-deduplicate:

===========
Deduplicate
===========

在使用 Scrapy 或其它工具开发爬虫时，数据去重一直是必要步骤，选择去重的方式也是各种各样：比如基于内存，基\
于文件，基于 redis，基于入库前 item 唯一字段查询，基于 url 请求指纹等。这里提供一些简单常用的方法，具体\
使用哪种方式请根据应用场景按需选择。

AyuItem
=======

本库实现的数据去重/更新的方式之一是通过 AyuItem 实现。可以很方便地通过 AyuItem 中的内置参数结合 mysql，\
mongodb，postgresql 和 oracledb 的唯一索引即可达到入库时自动判断数据是否已存在，不存在就新增插入，存在时\
也可自定义更新哪些字段或忽略它。而且是通过对应数据库的一条语句实现，减少像之前那样的先 select 再判断 insert，\
update 或忽略跳过它而造成的 io 延迟。比如：mysql 通过 INSERT INTO ... ON DUPLICATE KEY UPDATE 实现，\
mongodb 通过 $set 和 $setOnInsert 实现，postgresql 和 oracledb 是通过 MERGE INTO 实现。

.. versionadded:: 3.13.0

.. note::

   在此版本中内置了更简洁的去重及更新功能，可以通过设置 AyuItem 即可轻松达到之前先 select 然后再决定 \
   insert 还是 update 或什么也不做的复杂操作，且此方式实现方式更简洁且高效。具体的使用场景和 mongodb，\
   postgresql 和 oracle 数据的示例请在 DemoSpider 中查看。

.. versionchanged:: 3.18.0

.. note::

   在此版本之前，postgresql 是通过 INSERT INTO ... ON CONFLICT 实现数据的去重/更新的。目前可以使用和 \
   oracledb 一样的方式来保持易用性和统一。若需要维持旧的实现方式，只要在你的项目中把对应的 AyuAsyncPostgresPipeline \
   改为 AyuAsyncPostgresLegacyPipeline，把对应的 AyuFtyPostgresPipeline 改为 AyuFtyPostgresLegacyPipeline \
   把对应的 AyuTwistedPostgresPipeline 改为 AyuTwistedPostgresLegacyPipeline，即可保持与之前运\
   行效果一致的兼容效果。pg 数据库版本在 15 及以上可不用修改而无痛迁移。

.. warning:: 注意：使用 AyuItem 的自带数据去重/更新注意事项

   - Mysql 场景的实现基于 INSERT INTO ... ON CONFLICT 实现，所以一定要在 AyuItem 的 _update_rule \
     中对应的字段设置为唯一索引（如果 _update_rule 里有多条规则，那么需要创建对应的联合唯一索引）。

   - MongoDB，PostgreSQL 和 Oracle 同样推荐创建对应的唯一索引，来保证在数据量多时的效率，和防止并发场景\
     下的数据竞争导致插入相同数据。

Mysql
-----

对 mysql 的存储场景进行介绍：

.. note::

   - 使用 AyuItem 内置的 mysql 更新规则时，需要在 .conf 配置中设置其 odku_enable 为 True 才能激活\
     更新功能，而且 AyuItem 的 _update_rule 中的字段要设置为唯一索引才能生效（如果 _update_rule 是多\
     个字段才能定位到需要去重/更新的数据，那么对应的表中字段也要创建联合的唯一索引）；
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
     如果已匹配数据但是没有设置 _update_keys 则并不会更新任何字段；3.14.0 版本之后删除 _mongo_update_rule \
     和 _mongo_update_keys 旧字段参数，保持字段统一。

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

.. code-block:: python

   from ayugespidertools.items import AyuItem

   octree_item = AyuItem(
       octree_text=octree_text,
       octree_href=octree_href,
       start_index=index,
       _table=_save_table,
       _update_rule={"octree_text": octree_text},
       _update_keys={"octree_href"},
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

   from ayugespidertools.common.typevars import MysqlConf
   from ayugespidertools.utils.database import MysqlAsyncPortal


   async def test_example():
       conn = MysqlAsyncPortal(db_conf=MysqlConf(...))
       pool = await conn.connect()
       async with pool.acquire() as conn:
           async with conn.cursor() as cursor:
               await cursor.execute("SELECT 42;")
       await conn.close()

当然，也可以使用普通的方式来查询：

.. code-block:: python

   from ayugespidertools.common.typevars import MysqlConf
   from ayugespidertools.utils.database import MysqlPortal


   def test_example():
       conn = MysqlPortal(db_conf=MysqlConf(...)).connect()
       cursor = conn.cursor()
       cursor.execute("SELECT 42;")
       conn.close()

MongoDB
-------

MongoDB 场景下除了使用 AyuItem 的方式，也可以使用自定义的方式，推荐 asyncio 的方式。

.. code-block:: python

   from ayugespidertools.common.typevars import MongoDBConf
   from ayugespidertools.utils.database import MongoDBAsyncPortal


   async def test_example():
       db = MongoDBAsyncPortal(db_conf=MongoDBConf(...)).connect()
       res = await db["test_collection"].find_one({"key": "value"}, {"_id": 1})
       db.client.close()

当然，也可以使用普通的方式来查询：

.. code-block:: python

   from ayugespidertools.common.typevars import MongoDBConf
   from ayugespidertools.utils.database import MongoDBPortal


   def test_example():
       db = MongoDBPortal(db_conf=MongoDBConf(...)).connect()
       res = db["test_collection"].find_one({"key": "value"}, {"_id": 1})
       db.client.close()

PostgreSQL
----------

PostgreSQL 场景下的 asyncio 的数据库链接操作示例：

.. code-block:: python

   from ayugespidertools.common.typevars import PostgreSQLConf
   from ayugespidertools.utils.database import PostgreSQLAsyncPortal


   async def test_example():
       pool = await PostgreSQLAsyncPortal(db_conf=PostgreSQLConf(...)).connect()

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

   from ayugespidertools.common.typevars import PostgreSQLConf
   from ayugespidertools.utils.database import PostgreSQLPortal


   def test_example():
       conn = PostgreSQLPortal(db_conf=PostgreSQLConf(...)).connect()
       cursor = conn.cursor()
       cursor.execute("SELECT 42;")
       conn.close()

Oracle
------

Oracle 场景下的 asyncio 的数据库链接操作示例:

.. code-block:: python

   from ayugespidertools.common.typevars import OracleConf
   from ayugespidertools.utils.database import OracleAsyncPortal


   async def test_example():
       _sql = 'SELECT * from "_article_info_list"'
       pool = OracleAsyncPortal(db_conf=OracleConf(...)).connect()
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

   from ayugespidertools.common.typevars import OracleConf
   from ayugespidertools.utils.database import OraclePortal


   def test_example():
       conn = OraclePortal(db_conf=OracleConf(...)).connect()
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
