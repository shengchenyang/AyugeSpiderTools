.. _topics-configuration:

=============
Configuration
=============

AyugeSpiderTools 将项目中所依赖的敏感配置信息放入了当前项目 ``<project_dir>/<project_name>`` 的 \
VIT 下的 .conf 文件中独立管理。当然，你也可以在项目中自定义 VIT_DIR 参数来决定配置文件 .conf 的路径。

.. note::

   - VIT 是 very import things 的意思，VIT_DIR 路径下的 .conf 用于保存一些项目运行所依赖的重要配置\
     和自定义配置内容；
   - VIT_DIR 参数可以自定义，但此文件夹中的 .conf 文件不支持修改和自定义文件名。

若你有很多的 Scrapy 项目需要统一管理，可以选择以下方式：

- 如果是单机多项目的情况，你可以指定 VIT_DIR 参数为此机器上的统一地址即可。
- 如果是多机多项目的情况，更推荐使用本库的 consul 或 nacos 服务来远程配置和管理，灵活性更高。

下面来介绍 .conf 文件中的配置内容：

Introduction
============

.conf 文件配置格式使用 ini，具有易编写易解析易维护的优点，python 也有方便且成熟的自带库 `configparser`_ 支持。

[nacos]
=======

`Nacos`_ 可用于远程配置管理服务，可以更敏捷和容易地管理微服务平台。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "url", "_", "nacos 服务对应的链接，若有鉴权参数请在 url 中构建。"
   "format", "参数可选 json, xml, yaml", "nacos url 配置中对应的格式解析方法，支持 json，
   xml，yaml 解析。请优先使用 json 和 xml 来解析，yaml 解析需要安装 ayugespidertools[all] 依赖。"

[consul]
========

`Consul`_ 的配置管理功能同 nacos，是本库提供的另一选择。但请注意：consul 比 nacos 的优先级更高，如果\
两者都配置了会优先使用 consul 配置。不同的是配置中的鉴权 token 参数独立了出来。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "url", "_", "consul 服务对应的链接。"
   "format", "参数可选 json, xml, yaml, hcl", "consul url 配置中对应的格式解析方法，支持 json，
   xml，yaml，hcl 解析，推荐 json 解析格式。hcl 和 yaml 解析需要安装 ayugespidertools[all] 依赖。"
   "token", "可选，默认空", "consul token 参数。"

[mysql]
=======

用于 mysql 存储相关场景中使用，比如创建对应的 sqlalchemy 的 engine，engine_conn 来用于去重，创建数\
据库连接来解决表格缺失，字段缺失等问题。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "user", "_", "_"
   "password", "_", "_"
   "database", "_", "链接的数据库名称，在非 aiomysql 场景下，当 database 不存在时会用当前 user 创
   建所需库表及字段等。"
   "host", "可选，默认 localhost", "_"
   "port", "可选，默认 3306", "_"
   "engine", "可选，默认 InnoDB", "自动创建数据库和数据表时需要的参数"
   "collate", "可选，默认 utf8mb4_general_ci", "自动创建数据库和数据表时需要的参数"
   "charset", "可选，默认 utf8mb4", "自动创建数据库和数据表时需要的参数"
   "odku_enable", "可选，默认 false", "是否开启 ON DUPLICATE KEY UPDATE 功能"
   "insert_ignore", "可选，默认 false", "是否开启 INSERT IGNORE 功能"

.. note::

   - charset 参数选择有 utf8mb4，gbk，latin1，utf16，utf16le，cp1251，euckr，greek，charset \
     要与 collate 参数匹配。
   - 其中 engine，charset，collate 为自动创建数据库和数据表时需要的参数，可随意配置或默认即可，也可提\
     前手动创建好表，也可后续手动修改。

[mongodb:uri]
=============

mongodb 链接的 uri 配置方式。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "uri", "_", "mongoDB uri"

[mongodb]
=========

mongodb 链接的普通方式，[mongodb:uri] 和 [mongodb] 按需选择一种即可。 若两种都设置了，会优先从 mongodb:uri \
中获取配置。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "database", "_", "_"
   "user", "_", "_"
   "password", "_", "_"
   "host", "可选，默认 localhost", "_"
   "port", "可选，默认 27017", "_"
   "authsource", "可选，默认 admin", "_"
   "authMechanism", "可选，默认 SCRAM-SHA-1", "_"

[postgresql]
============

用于 postgresql 存储相关场景中使用，比如创建对应的 sqlalchemy 的 engine，engine_conn 来用于去重，\
创建数据库连接来解决表格缺失，字段缺失等问题。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "user", "_", "_"
   "password", "_", "_"
   "database", "_", "_"
   "host", "可选，默认 localhost", "_"
   "port", "可选，默认 5432", "_"
   "charset", "可选，默认 UTF8", "同 mysql 一样，用于在表不存在而创建时需要，可随意配置，后续也可手动修改。"

[elasticsearch]
===============

用于 elasticsearch 存储相关场景中使用，也具有对应的 es_engine，es_engine_conn 来用于存储前的去重\
(查询及更新等自定义)逻辑。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "hosts", "_", "若有多个，用逗号分隔，比如 https://x.x.x.x:9200,https://x.x.x.x:9201"
   "index_class", "默认 {'settings':{'number_of_shards': 2}}", "es Document 中的配置"
   "user", "默认 elastic", "_"
   "password", "默认 elastic", "_"
   "init", "是否初始化 es Document，默认 false", "是否创建 es 索引，此设置一般只在第一次运行项目时
   打开，或者选择手动创建并配置此参数永远为 false。"
   "verify_certs", "默认 false", "证书验证，推荐开启"
   "ca_certs", "默认 None", "ca_certs 路径"
   "client_cert", "默认 None", "client_cert 路径"
   "client_key", "默认 None", "client_key 路径"
   "ssl_assert_fingerprint", "默认 None", "es 启动中的 HTTP CA certificate SHA-256 fingerprint 参数"

.. note::

   - ca_certs，client_cert，client_key，ssl_assert_fingerprint 中只用配置一个即可，若 verify_certs \
     设置为 false 则都不用配置以上参数，但推荐开启此参数。
   - index_class 配置中不建议包含 name 参数，而是通过 AyuItem 中的 _table 来设置，AyuItem 会覆盖 \
     index_class 中的 name 配置。

[mq]
====

推送到 RabbitMQ 场景所需的参数。以下配置参数与 `pika`_ 和 `aio-pika`_ 中一致，请自行对照查看。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "virtualhost", "_", "_"
   "queue", "_", "_"
   "exchange", "_", "_"
   "routing_key", "_", "_"
   "username", "可选，默认 guest", "_"
   "password", "可选，默认 guest", "_"
   "host", "可选，默认 localhost", "若有多个，用逗号分隔。比如 x.x.x.x,y.y.y.y"
   "port", "可选，默认 5672", "_"

.. warning::

   在 ayugespidertools 版本 3.11.2 及以上，只有 AyuMQPipeline (pika) 才支持 host 通过 , 分割来\
   适配集群模式；而 AyuAsyncMQPipeline (aio-pika) 的场景不支持以逗号分隔的 host 参数，若需要集群支\
   持请查看 aio-pika 文档。为了通用性，你可以将 AyuMQPipeline 的集群模式设置的和 AyuAsyncMQPipeline \
   一样。

.. note::

   以上内容是在标准场景下的配置，但是有时候用户只想推送到 queue 中而不关心或不绑定到 exchange，那么就存\
   在两种情况，接下来分别介绍这两种场景。

如果是标准场景，推送的 queue 有绑定的 exchange，那么你需要完整地配置他们，示例如下：

.. code-block:: ini

   [mq]
   virtualhost=这里填入 virtualhost
   queue=这里填入推送到的 queue
   exchange=这里填入推送到的 queue 所绑定的 exchange
   routing_key=这里填入绑定时的 routing_key
   username=guest
   password=guest
   host=localhost
   port=5672

当不需要绑定 exchange 时，这时候需要注意，如果 ayugespidertools 版本在 3.11.1 及以下，需要的配置示例\
如下：

.. code-block:: ini

   ; 需要将 exchange 设置为空，routing_key 设置与 queue 值一致。
   [mq]
   virtualhost=ayuge
   queue=ayuge_sec_queue
   exchange=
   routing_key=ayuge_sec_queue
   username=guest
   password=guest
   host=localhost
   port=5672

如果 ayugespidertools 版本在 3.11.2 及以上，需要的配置更简约，示例如下：

.. code-block:: ini

   ; 不需要的 exchange 和 routing_key 参数可以移除了，或者注释掉它们。
   [mq]
   virtualhost=这里填入 virtualhost
   queue=ayuge_sec_queue
   username=guest
   password=guest
   host=localhost
   port=5672

.. note::

   旧写法依然适用于最新的版本，只是最新的写法更加易维护，不必担心兼容问题。

[oracle]
========

用于 oracle 存储相关场景中使用，比如创建对应的 sqlalchemy 的 engine，engine_conn 来用于去重，但不会\
处理数据库表及字段缺失等错误，请提前创建好，因为其部分报错不如 mysql 及 postgresql 那样清晰明了，虽然也\
能解决，但必要性不高。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "user", "_", "_"
   "password", "_", "_"
   "service_name", "_", "_"
   "host", "可选，默认 localhost", "_"
   "port", "可选，默认 1521", "_"
   "encoding", "可选，默认 utf8", "oracledb 的链接参数。"
   "thick_lib_dir", "可选，默认 false", "oracledb 的 thick_mode 所需参数，按需配置。"
   "authentication_mode", "可选，默认 DEFAULT", "oracledb 的 authentication_mode 所需参数，按需配置。"

[kafka]
=======

推送到 kafka 场景所需的参数。以下配置参数与 `kafka-python`_ 中一致，请自行对照查看。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "bootstrap_servers", "若有多个，用逗号分隔。比如 x.x.x.x:9092,x.x.x.x:9093", ""
   "topic", "_", "_"
   "key", "_", "_"

[kdl_dynamic_proxy]
===================

快代理动态代理配置参数。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "proxy", "_", "快代理动态代理 api。"
   "username", "_", "_"
   "password", "_", "_"

[kdl_exclusive_proxy]
=====================

快代理独享代理配置参数。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "proxy", "_", "快代理独享代理 api。"
   "username", "_", "_"
   "password", "_", "_"
   "index", "可选，默认 1", "表示取其索引值对应的代理。"

[oss:ali]
=========

上传到阿里云 oss 的配置参数。

.. csv-table::
   :header: "参数名", "参数备注", "描述"
   :widths: 10, 15, 30

   "access_key", "_", "阿里云 access_key_id"
   "access_secret", "_", "阿里云账号对应的 access_key_secret"
   "endpoint", "_", "填写 Bucket 所在地域对应的 Endpoint"
   "bucket", "_", "Bucket"
   "doc", "_", "需要操作的文件夹目录，比如 file/img，为可选参数。"
   "upload_fields_suffix", "规则字段，默认为 _file_url", "上传到 oss 的字段规则，包含
   upload_fields_suffix 后缀的字段会上传到 oss。"
   "oss_fields_prefix", "规则字段，默认为 _ ", "上传到 oss 的字段生成的新字段规则，会在原字段添加
   oss_fields_prefix 前缀。"
   "full_link_enable", "是否开启完整链接，默认 false", "为是否保存完整的 oss 文件链接。"

.. note::

   遵守规则时的 oss 上传逻辑时使用，详细介绍请在 :ref:`item 的规则 <topics-items-yield-item>` 部\
   分中查看，更复杂的需求也可根据示例自行实现。具体请看 demo_oss，demo_oss_sec 和 demo_oss_super 的\
   场景示例。请自行选择可接受的风格。

[custom_section]
================

用于自定义配置：

.. note::

   - 一些 scrapy 第三方扩展需要在 settings.py 中设置一些配置，涉及到 host，密码等隐私配置，直接展示\
     在 settings.py 里是不可接受的，这里提供一种方法来解决；
   - 注意：你可以在 .conf 中配置多个自定义部分来满足不同场景。

在 settings.py 或 spider 等脚本中赋值重要参数时，可以从 VIT_DIR 的 .conf 中获取自定义配置内容，来达\
到隐藏隐私内容和保持配置内容统一存放的目的；比如在 .conf 中自定义配置以下内容：

.. code:: ini

   [custom_section]
   custom_option=custom_value
   custom_int=1
   custom_bool=true
   custom_float=3.1415926

那么，可以在程序任意地方通过 get_cfg 来获取自定义部分：

.. code-block:: python

   from ayugespidertools.config import get_cfg

   _my_cfg = get_cfg()
   custom_option = _my_cfg["custom_section"].get("custom_option", "no_custom_value")
   custom_int = _my_cfg["custom_section"].getint("custom_int", 0)
   custom_bool = _my_cfg["custom_section"].getboolean("custom_bool", False)
   custom_float = _my_cfg["custom_section"].getfloat("custom_float", 3.14)

.. _configparser: https://docs.python.org/3/library/configparser.html
.. _Nacos: https://nacos.io
.. _Consul: https://consul.io
.. _pika: https://pika.readthedocs.io/en/stable/
.. _aio-pika: https://docs.aio-pika.com/
.. _kafka-python: https://kafka-python.readthedocs.io/en/master/
