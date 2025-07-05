.. _additional-news:

=============
Release notes
=============

AyugeSpiderTools 3.12.4 (Preview: TBD)
======================================

此部分用于展示下一版本更新预览。

这是预发布版本，部分内容还处于待定状态，和最终正式版可能会有所不同（包括版本号），不建议在生产环境中使用，\
可自行打包来提前测试和体验。

打包参考教程请查看：`How-To-Build-Your-Own-Library`_

.. _How-To-Build-Your-Own-Library: https://ayugespidertools.readthedocs.io/en/latest/diy/myself.html

当然也可以直接 ``pip install git+https://github.com/shengchenyang/AyugeSpiderTools.git`` 来\
安装预发布包。

... ...

AyugeSpiderTools 3.12.3 (2025-07-06)
====================================

New features
------------

- scrapy 依赖更新为最新的 2.13.3。

  (:commit:`2315301f5ea1dd2fc48162c86837085a1cc71661`)

Code optimizations
------------------

- 去除多余的依赖。

  (:commit:`2315301f5ea1dd2fc48162c86837085a1cc71661`)

AyugeSpiderTools 3.12.2 (2025-06-22)
====================================

New features
------------

- python 3.13 support。

  (:commit:`1a221d90061addc68f6feed98043e83267c95cbd`)

Code optimizations
------------------

- 添加 github action 打包上传的流程。

  (:commit:`1a221d90061addc68f6feed98043e83267c95cbd`)

AyugeSpiderTools 3.12.1 (2025-06-15)
====================================

New features
------------

- oracle 存储场景添加 authentication_mode 的配置参数，默认 DEFAULT 与旧版本保持一致。

  (:commit:`511821177288cd7e2499dd3f87943399388e1bf7`)

- aiohttp 请求的场景支持 yarl.URL 类型参数。

  (:commit:`8727d69f58bd6b59d9e1dc9e3d80ed2575d38a39`)

- scrapy 依赖更新为最新的 2.13.2。

 (:commit:`50e2a23a3715fbdb8318b457d8162590f3f2ce27`)

Bug fixes
---------

- 解决文件下载本地的场景未保存的问题。

  (:commit:`614f3d670718badd27618b134e66d6c783ca114a`)

AyugeSpiderTools 3.12.0 (2025-05-20)
====================================

Deprecations
------------

- DATABASE_ENGINE_ENABLED 配置项弃用声明，我将在新方法 ayugespidertools.utils.database 稳定后的\
  下一个 major 版本（且在至少半年之后）才会考虑删除它。

  (:commit:`1430dfaa9e06335eaf3d237d777e1ed84f14b7a6`)

New features
------------

- scrapy 依赖更新为最新的 2.13.0。

  (:commit:`a8dd8d306c3bdc9cfd1e1019fbbc552243311b4a`)

- 生成的模版修改为 scrapy 新版本推荐的风格写法。

  (:commit:`c7929064c5fcf5076e6a9eaec3aed57a23b4f0f6`)

- 添加 Mysql, MongoDB，PostgreSQL 的链接管理，方便创建和使用当前配置中的数据库链接。

  (:commit:`1430dfaa9e06335eaf3d237d777e1ed84f14b7a6`)

- 添加根据 redis 查询去重的基础方法。

  (:commit:`ae657fc7ba50d758fe3f773f4357252fd132ce70`)

- 添加 Mysql INSERT IGNORE 的配置选项，默认与旧版本保持一致。

  (:commit:`84004430f619a6d9dbe08c54774773833bf2fd4c`)

Code optimizations
------------------

- 更新 ci/cd 依赖库版本，文档依赖及版本。

  (:commit:`42e8e699f327bb65d64e4d1346b0b19fdfbcdb66`)

- 解决一些 type hint, mypy check 和文档的问题。

AyugeSpiderTools 3.11.2 (2025-03-30)
====================================

New features
------------

- 添加 mq(aio-pika) 的 async 管道模版示例。请在 DemoSpider 中 demo_mq_async 或文档中查看具体使用方法。

  (:commit:`674bee7e0cdf18bf4259d4565cd4eaa291b49584`)

- 添加 mq(pika) 管道的集群支持。

  (:commit:`1519296eef3df55d2c2a3b9a1273e50500afc075`)


Code optimizations
------------------

- mq pipeline 场景下的 .conf [mq] 部分配置更清晰。

  (:commit:`5298b94973721a6ce984e54c35f9c21316d6168e`)

- 固定 ci 的依赖库版本，使测试更稳定。

  (:commit:`ba0ed58dc783c8bf210edaa03b1fdc8c16b3e911`)

AyugeSpiderTools 3.11.1 (2025-01-31)
====================================

Deprecations
------------

- 删除 ROBOTSTXT_OBEY 模式配置。

  (:commit:`04ebb6759cc15ef921eb778a7be6d39bb6c3b468`)


Code optimizations
------------------

- 生成模版中添加日志 remove 示例。

  (:commit:`974b2dd973998fbd2795305c827ebe14a750d007`)
- 添加 AiohttpRequest 参数弃用警告。

  (:commit:`3d34e9913529683bb7d4295b240f1bc0bf529f7a`)
- 完善 poetry 开发流程。

  (:commit:`8c82a6bb020f124751e088cfb2c150059b31df0f`)
- 优化 VIT_DIR 的获取方式。

  (:commit:`9a978e7dbd68e0b54cf06d97e22f3027fcd49fd2`)

  (:commit:`ecbdbb0c860c14292769a100a6f7e55f4a909edd`)
- middlewares 和 pipelines 模块添加延迟加载功能。

  (:commit:`37ba57bca3d813f6e6f5aa93f40871c4e0dd8900`)
- 将文档格式由 md 转为 rst。

  (:commit:`f78e4b89cd0bdacb2560b5be5f71681cd915cd7c`)
- 添加和优化 pyupgrade，Makefile，exception 模块。

  (:commit:`b84d6b9ccaa865c669056420c0e275714a60854a`)

  (:commit:`4251401f6e761e189cceeb74608360d151547208`)

  (:commit:`9e266c0551bf2e0d1e84faebbf04209d04ff2def`)

AyugeSpiderTools 3.11.0 (2024-11-29)
====================================

Deprecations
------------

- 移除对 python3.8 的支持。

  (:commit:`104a3faa0877a72febd960d110d349ec9be22239`)
- 不再支持 3.4 及以下版本的 `mongodb` 的存储，

  (:commit:`2874aabadb5149cbc376aa78e78077555309084b`)

New features
------------

- scrapy 依赖更新为最新的 2.12.0。

  (:commit:`c3cf229179e86fab4b7800bbd8dacfb408382f83`)
- 升级 aiohttp 依赖版本，解决升级后的兼容问题。

  (:commit:`9f6b68e77ffed45d6a2721678573b9fc9c63700e`)

  (:commit:`62160a8e3b3eb355a429bbaedfc6d05e771368ab`)

Bug fixes
---------

- 解决 psycopg 相关依赖可能存在的冲突问题。

  (:commit:`a267c03aec55ed63a16926f90cf3d22e9ca20611`)

Code optimizations
------------------

- 项目改为基于 python 3.9 开发，将涉及到的开发代码，ci/cd，测试等工具都改为 3.9 的特性。

  (:commit:`1e44c3f9f4fee29f305da929413b2aa1774e319b`)

AyugeSpiderTools 3.10.1 (2024-10-19)
====================================

Deprecations
------------

- mongodb 场景统一存储相关的代码逻辑，且更新方式由之前 update_many 改为更正常的 update_one 的规则。

  (:commit:`8af915f65fa021a97b2eeaf9893167f511ce81b9`)

.. note::

   - 虽然此版本为 patch 升级，但还请在虚拟环境中自行测试后再确认是否升级。

New features
------------

- 无。

Bug fixes
---------

- 解决 macOS 低版本的依赖兼容问题，优化依赖管理；解决 mongodb 存储在 py3.11 及以上场景时 motor 和 \
  pymongo 的版本冲突造成的运行报错。

  (:commit:`a52755fc1e3b75728f09a04017b5907afa161624`)

Code optimizations
------------------

- 整理代码风格。

  (:commit:`c080c3ccf0e0796c728dc8e25562b2d90f79e72d`)

  (:commit:`213009271ab66ce6ec846462db0db0afe0f068dd`)

<hr>

AyugeSpiderTools 3.10.0 (2024-10-01)
====================================

Deprecations
------------

- 将 ``ayugespidertools.common.utils`` 中 ``ToolsForAyu`` 修改为 Tools。

  (:commit:`73703a0cbf26e53813bb58db83e89fe55486a3e1`)

- 删除 ``AiohttpFormRequest``，``AiohttpRequestArgs``，改为更简洁的 ``AiohttpRequest`` 且与 \
  aiohttp 请求参数一致。

  (:commit:`1a7b1000fe32abe249007533a65f891bd989aee9`)

- 整理并统一了 ``ayugespidertools.common.multiplexing`` 中 ReuseOperation 的函数参数名。

  (:commit:`1cad13a94449dafa2f988fdd825fe282c2368dec`)

.. note::

   - 以上变动比较影响用户的是 AiohttpRequest 的部分，为不兼容的重构部分。其它部分如果未在项目中使用则\
     完全不影响库的正常运行。
   - AiohttpRequest 新功能介绍文档请在 :ref:`ayugespidertools aiohttp <topics-downloader-middleware-aiohttp>` 中查看。

New features
------------

- 升级 ua 数据为新版本，并且将其放入 data 中的 browsers.json 文件中，修改获取 ua 的方式。

  (:commit:`7d08f853a7ca0ad9b860a8cc0e550c1b0b66e2f0`)

  (:commit:`7a905a3403801bb6ed0d453d6d87698eb0fd4ce4`)

- oss 上传文件资源场景支持列表类型，现在可通过 mongodb 存储场景将 oss 相关的 AyuItem 字段设置为列表\
  类型，在 `demo_oss_super <https://github.com/shengchenyang/DemoSpider/blob/3.10.x/DemoSpider/spiders/demo_oss_super.py>`_ \
  中查看示例。

  (:commit:`5946c54144f30503090d7f09ec6a88a0b66427f9`)

  (:commit:`e553152773f9fe7aee1fdd118a9bb6327daf52ef`)

- 增加从 VIT_DIR 中 .conf 的 ini 配置解析方法 get_cfg，以方便配置统一存放管理和保护隐私，在 \
  `demo_conf <https://github.com/shengchenyang/DemoSpider/blob/3.10.x/DemoSpider/spiders/demo_conf.py>`_ \
  中查看示例。

  (:commit:`dd2485bf28ddf4cc9a08b464f9baf7af39bf7587`)

- aiohttp 请求方式改为更人性化的，且与 aiohttp 请求参数保持一致的体验。以减少用户使用，理解和维护成本。

  (:commit:`1cad13a94449dafa2f988fdd825fe282c2368dec`)

.. note::

   - 其它存储场景的 oss 暂不支持列表形式，需自行实现，可自行按照示例添加自行打包。

Bug fixes
---------

- 修复轨迹生成时关于抖动出错的问题。

  (:commit:`6ad69583647fc3a4261f7a4ad4521c22580cc1ab`)

- 修复自使用的 json 解析方法的错误。

  (:commit:`a1d7aac2c826807c4838e4fbd31de6e637cab963`)

.. note::

   - 这里的问题修复都是非框架主要功能，不影响 scrapy 的扩展功能使用。

Code optimizations
------------------

- 升级 aiohttp 依赖版本。

  (:commit:`5b448e5991cd7e26b6702cdbd1bfcacc9b3ebcce`)

- Makefile 添加 git 相关的配置。

  (:commit:`6304b772b14daf0880b591e82ff182a66c77bd2e`)

- 解决文档 ``Edit on GitHub`` 出现的链接不对的问题。

  (:commit:`6a79f617eb8d0e6834f673199d1ab08f68681df3`)

- 文档完善贡献部分。

  (:commit:`842300ad38afd9169e70e2c839128d282a120508`)

- 优化 get_items_except_keys 方法，提升效率。

  (:commit:`d2181444982995421f34c406e51ca0a053f9db1f`)

<hr>

AyugeSpiderTools 3.9.8 (2024-05-17)
===================================

Deprecations
------------

- 删除新建项目中 pyproject.toml 模板。

  (:commit:`bb0adf3083cfdbeace76ddb96c9ac35a6dc4f76d`)

- 删除新建项目中 run.py, run.sh, README.md, requirements.txt 模板的过度设计，不影响程序功能，按需\
  自行添加。

  (:commit:`2a02faa385069ac3a93194296c326dc31228c47b`)

  (:commit:`cb1393f70f49e4f956adecc4be5126871a97c3df`)

- 更新 spider 模板内容，保证示例的稳定，为了通用性去除 type hint（请按需自行添加，DemoSpider 项目中\
  有示例），并规避一些问题等。

  (:commit:`7dc45fda8af3270d713fc21d9feda3ca8d6ea739`)

- EncryptOperation 改名为 Encrypt，不影响库的使用。

  (:commit:`5e529ca3eb625637894712a3972ba95a612c1526`)

- 删除库中未使用的 get_files_from_path 方法。

  (:commit:`e0d04d27a5b1a58eabe785485ed3402f0748c892`)

.. note::

   - 此弃用和变动并不影响项目中的功能，只涉及一些自动生成的多余配置文件，运行文件等，这些为过度设计（不应\
     替用户强行决定，且未做到完美适配）。
   - 比较喜欢完整项目模版的开发者，则可选择通过 `LazyScraper <https://github.com/shengchenyang/LazyScraper>`_ \
     项目来更方便地生成项目模版。

New features
------------

- 同步更新 scrapy 依赖版本为 2.11.2。

  (:commit:`1618654d4c2b9bd4032a52844e29abe17d2ee532`)

Bug fixes
---------

- 无。

Code optimizations
------------------

- requests 相关代码更换为 urllib 方式。

  (:commit:`f01403012bcebce0e49c27840dff446aa7ef70fd`)

  (:commit:`5cd28ccd6f38d1a37b2d57cf7bc1306c13173d1e`)

- .conf 模板格式整理，修改模板为英文，以解决中英文混编下的格式问题。

  (:commit:`f6f0e43bd5fcced5f724882606941fd033a56156`)

  (:commit:`01d02a19ee275fe80c52d696dee39500d35c9581`)

  (:commit:`8ded926de0a04680ce91fd07bfde36d478bfda5e`)

- 添加 .editorconfig 配置。

  (:commit:`d175c6e0ddfaf3dcc105c62ada422c9f907388cb`)

- `poetry` 依赖更新。

  (:commit:`f78354616c3e95d8e00238e8970fe332373a0273`)

- 文档更新。
- mongodb 存储场景中 pymongo 依赖版本及应用场景的判定逻辑修改，由通过 py 版本来判定改为由 pymongo 依\
  赖版本来判定。目前本库在 py3.11 及以上还是会安装 ``^4.5.0`` 版本的 pymongo，不影响旧项目功能。

  (:commit:`625ad1cf3a16463aa77744b7ce4d46f94f056bab`)

.. note::

   补充解释：若 py 3.11 及以上则使用 ``^4.5.0`` 版本的 pymongo 来支持 3.6 及以上版本的 MongoDB 来\
   解决 motor 的异步存储问题；若 py3.11 以下则使用 3.13.0 的 pymongo 版本来与目前一致。(:issue:`11`)

<hr>

AyugeSpiderTools 3.9.7 (2024-03-08)
===================================

Deprecations
------------

- 无。

New features
------------

- oss 场景添加是否保存完整链接的配置 full_link_enable，默认 false，不影响旧项目。

  (:commit:`009ac20a4db55069c4b0cee5822834e42e21ba00`)

- oss 场景不再需要手动添加上传的字段是否为空的判断。

  (:commit:`009ac20a4db55069c4b0cee5822834e42e21ba00`)

Bug fixes
---------

- 修复 `aiohttp` 场景下由于目标网站未遵守编码时可能会出现的编码问题。

  (:commit:`d2772b5960c972c4cc6ee6e6ce541fa00e34a7fb`)

Code optimizations
------------------

- 添加 aiohttp 可支持的请求方式。

  (:commit:`c7c247e1badf411a149d9d6e1430230ec81e99a8`)

- 优化 oss, file download 场景的 pipeline 示例，减少复杂逻辑。

  (:commit:`b0929d8adba7c4d3ce2c7064a56656825d8802b7`)

  (:commit:`f0f1b2f61e449e30812d7410e55652d4fcb42169`)

- 测试场景增加剔除无关代码块的规则。

  (:commit:`3e0ce949340b8d27f95d86ecbcbd8bf04e85cccd`)

- 代码风格统一，补充缺失的 type hint，提升开发体验。

<hr>

AyugeSpiderTools 3.9.6 (2024-02-18)
===================================

Deprecations
------------

- 无。

New features
------------

- 无。

Bug fixes
---------

- 修复 mysql 存储引擎 engine 参数未生效的问题。

  (:commit:`1240e375dd4e1bc7c87ba876a3cc8faf34b8695f`)

Code optimizations
------------------

- 更新 aiohttp 依赖库版本以解决破坏兼容性的问题，同步更新 scrapy 依赖版本。

  (:commit:`3f0dc5ada3a9742eff54e8a77c03a4fb7906795d`)

  (:commit:`246c824813b4ffdc844b0df26a9e944a467fb9ea`)

- 文档更新。

<hr>

AyugeSpiderTools 3.9.5 (2024-01-30)
===================================

Deprecations
------------

- 无。

New features
------------

- mysql 场景添加 odku_enable 配置来设置是否开启 ON DUPLICATE KEY UPDATE 功能。

  (:commit:`25d71ddb789c71f3f570f85576ff225aeaf58d7b`)

- 添加 oss pipeline 的示例，请在 DemoSpider 中 demo_oss 和 demo_oss_sec 查看具体使用方法。

  (:issue:`16`)

Bug fixes
---------

- 解决文件下载不支持多字段下载的问题，请在 DemoSpider 中 demo_file 和 demo_file_sec 查看具体使用方法。

  (:commit:`f836f02d3c15b57623851888c0451ea0bfe8c631`)

  (:commit:`f504c45b86f2e328e2a9bb9f61328b693a571b52`)

- 解决远程配置管理中缺失的 `mongodb:uri` 优先级设置。

  (:commit:`51ea7da83c81fe97ea5cd6a6500fdb7fc3fa233b`)

Code optimizations
------------------

- mq 场景添加关闭链接处理。

  (:commit:`ac54fd0a7611a8e63b46689da83718a9cebdb013`)

- 更新 readthedocs 中的教程指南，以方便快速上手。
- 更新部分依赖库版本。

<hr>

AyugeSpiderTools 3.9.4 (2024-01-10)
===================================

Deprecations
------------

- 无。

New features
------------

- 添加 `elasticsearch` 支持，具体示例请在 `DemoSpider` 中 `demo_es` 和 `demo_es_async` 查看。

  (:issue:`15`)

  (:commit:`c4d048ee74c7246760e2ba91ef2844a5dd3540d7`)

  (:commit:`7651dd32974f6362b9a2dbc8e7258a5528d98858`)

Bug fixes
---------

- 无。

Code optimizations
------------------

- mypy check。

  (:commit:`785e36a5a85b141168ce24bfae9efe605ac05c36`)

<hr>

AyugeSpiderTools 3.9.3 (2023-12-30)
===================================

Bug fixes
---------

- 解决 ``pip install ayugespidertools`` 并执行简单场景时提示 oracledb 的依赖缺失问题。

  (:commit:`e363937f2de8cb5dd06938ca2eb470e1a5b08847`)

Code optimizations
------------------

- 统一代码风格。

  (:commit:`ecb97e803b36da5a5fd0bca14c98654a4b5d743b`)

<hr>

AyugeSpiderTools 3.9.2 (2023-12-28)
===================================

New features
------------

- mysql 配置项支持自定义自动创建库表场景的 engine 和 collate 参数。

  (:commit:`e6526668b818ec0d442160e60a98b73bd45fb673`)

Bug fixes
---------

- 解决 `settings` 模板生成的 `LOG_FILE` 不是当前项目名的问题。

  (:commit:`93c19d6c6812a86f6ea1ece7618c98e0f8c63957`)

Code optimizations
------------------

- 更新 spider 模板，模板中解析方式改为 scrapy 的形式，防止对开发者造成理解成本。

  (:commit:`91ad948506495bee210a673cd08541329375d8c4`)

- 更新 `spider` 模板中的 `type hint`，优化了开发者使用体验。

  (:commit:`c2a09087f9b9fa1d20927d51f9e9f670c74d00f3`)

- 优化一些数据库连接处理和配置解析方法等。

<hr>

AyugeSpiderTools 3.9.1 (2023-12-22)
===================================

New features
------------

- 添加 postgresql 的 asyncio 的 AsyncConnectionPool 存储场景支持。

  (:commit:`341e7681931f796b5167696b948ea331e2b62dbb`)

Bug fixes
---------

- 解决 asyncio 协程场景下的 spider 的 AyuItem 写法风格不兼容的问题。

  (:commit:`66177e402d0e9c15b559664bfc40c6de0e545735`)

Code optimizations
------------------

- 更新 spider 模板示例。

  (:commit:`61e10b140e880c7b2348b35687c167b6fad99b99`)

<hr>

AyugeSpiderTools 3.9.0 (2023-12-18)
===================================

Deprecations
------------

- AsyncMysqlPipeline 改名为 AyuAsyncMysqlPipeline。
- AsyncMongoPipeline 改名为 AyuAsyncMongoPipeline。
- 删除 oss 的模块及依赖。

New features
------------

- 添加 oracle 的存储场景支持，目前有 fty 及 twisted 两种方式。
- 添加 mongodb:uri 的配置方式。

Bug fixes
---------

- 解决 asyncio mysql 协程场景下可能会出现的被垃圾回收而阻塞的问题。
- 解决 mysql 或 postgresql 的错误处理场景下由于权限等问题造成的循环递归问题。

Code optimizations
------------------

- 优化 .conf 模板示例，配置更明确且更易管理。
- mypy check.

<hr>

AyugeSpiderTools 3.8.0 (2023-12-03)
===================================

Deprecations
------------

- MYSQL_ENGINE_ENABLED 的配置项名改为 DATABASE_ENGINE_ENABLED，目前支持 msyql 和 postgresql。
- 安装再添加 database 选项，可通过 pip install ayugespidertools[database] 安装所需的所有数据依赖及扩展。

.. warning:: 注意：此变更包含不兼容部分，需要着重注意的部分如下：

   - 删除了 MYSQL_ENGINE_ENABLED 配置项；
   - 由于 SQLAlchemy 依赖升级到了 2.0+ 新版本，与以往的去重使用有变化，具体请查看本库 readthedocs 文档。

New features
------------

- 支持 python3.12。
- 添加 postgresql 的存储场景支持，目前有 fty 及 twisted 两种方式。
- DATABASE_ENGINE_ENABLED 的配置目前会激活对应场景中数据库的 engine 和 engine_conn 以供去重使用。
- 将 psycopg 相关的数据库扩展依赖改为可选项，可通过 pip install ayugespidertools[database] 安装所需依赖。

Code optimizations
------------------

- 优化 type hints。
- 更新生成脚本模板以匹配新版本，也可使用以往 pandas 去重方式。
- 更明确的日志信息。

<hr>

AyugeSpiderTools 3.7.0 (2023-11-23)
===================================

Deprecations
------------

- 获取 nacos 和 consul 中的配置时不再转小写，请按照 readthedocs 示例填写。
- 删除 html2text 相关依赖及代码，此场景更适合自行实现。
- 安装不再包含非核心依赖，可通过 pip install ayugespidertools[all] 安装全部依赖。
- 一些 api 变动：

.. csv-table::
   :header: "更改前", "更改后", "受影响的部分"
   :widths: 10, 15, 30

   "extract_html_to_md", "删除", "ayugespidertools.formatdata"
   "AliOssBase", "转移到 ayugespider.extras 中", "ayugespidertools.oss"
   "yidungap, imgoperation, verificationcode", "转移到 ayugespider.extras 中，并整理在一起", "ayugespidertools.imgoperation; \
   ayugespidertools.verificationcode; ayugespidertools.common.yidungap"

- 以下是对 extras 相关模块所影响较大部分的介绍：

.. csv-table::
   :header: "更改前", "更改后", "受影响的部分"
   :widths: 10, 15, 30

   "YiDunGetGap.discern", "CvnpilKit.discern_gap", "ayugespidertools.common.yidungap"
   "Picture.identify_gap", "CvnpilKit.identify_gap", "ayugespidertools.imgoperation"
   "match_img_get_distance", "CvnpilKit.match_gap", "ayugespidertools.verificationcode"
   "get_normal_track", "CvnpilKit.get_normal_track", "ayugespidertools.verificationcode"
   "get_selenium_tracks", "ToolsForAyu.get_selenium_track", "ayugespidertools.verificationcode"

.. warning::

   - 此变更包含不兼容部分，如果你只使用其中 scrapy 扩展库部分，那么除了 nacos，consul 的 yaml 和 hcl \
     解析外对你无影响。
   - 再次提醒，使用时请做好依赖管理，以免不兼容部分对你的影响！

New features
------------

- mongo 场景添加 authMechanisem 配置选项，为可选配置，默认为 SCRAM-SHA-1。
- 将 numpy, oss, pillow 等非核心依赖改为可选项，可通过 pip install ayugespidertools[all] 安装所有依赖。

Code optimizations
------------------

- 优化 aiohttp, cvnpil 等测试用例，将图像相关功能整理并放入 cvnpil 模块中。
- ayuge version 修改为从 __version__ 获取信息的方式。
- 更新模板，mysql_engine 的示例改为通过 sqlalchemy 的方式，减少依赖数且大部分场景运行效率更好。
- 将可选装依赖的相关的功能代码统一放入 extras 中，更易管理。

<hr>

AyugeSpiderTools 3.6.1 (2023-11-06)
===================================

Bug fixes
---------

- 解决 mq 推送场景时 yield AyuItem 时的错误，现可支持多种格式。
- 解决 VIT_DIR 默认参数未存储至 settings 中的问题。


Code optimizations
------------------

- 文件下载场景添加 FILES_STORE 路径不存在时的自动创建处理。
- settings 模板删除无关配置。
- 项目添加 question issues template。

<hr>

AyugeSpiderTools 3.6.0 (2023-10-31)
===================================

Deprecations
------------

- 一些 api 变动：

.. csv-table::
   :header: "更改前", "更改后", "受影响的部分"
   :widths: 10, 15, 30

   "删除 LOGURU_CONFIG 配置参数", "现只需配置 `LOGURU_ENABLED` 即可", "slog 日志模块"
   "删除 spider 中 settings_type 参数", "此为过度设计，若需要可自定义配置", "项目配置信息"
   "删除 spider 中 mysql_engine_enabled 参数", "转移到设置中，名称为 MYSQL_ENGINE_ENABLED", "配置模块，影响较大"
   "AyuItem 中 _table 参数类型修改", "修改为与普通字段一样的 DataItem 或 str 类型，删除 demand_code 字段", "spider，Item 模块"
   "删除 spider 中 custom_table_enum 参数", "CvnpilKit", "同上"
   "删除 RECORD_LOG_TO_MYSQL 配置参数", "改为 ayugespidertools.pipelines.AyuStatisticsMysqlPipeline 方式调用", "配置模块"
   "YiDunGetGap", "CvnpilKit", "ayugespidertools"
   "YiDunGetGap", "CvnpilKit", "ayugespidertools"

.. warning::

   此变更包含不兼容内容，请修改不兼容部分并调试正常后再投入生产；本项目在有一些不兼容变更时，会发布 Minor \
   及以上的版本包，请做好依赖版本管理

Code optimizations
------------------

- 设置 VIT_DIR 默认参数。
- 去除冗余配置，统一配置风格。将一些过于复杂的模块拆分，便于管理。

<hr>

AyugeSpiderTools 3.5.2 (2023-10-17)
===================================

New features
------------

- 添加从 nacos 中获取配置的方法，若 .conf 中同时存在 consul 和 nacos 配置则优先使用 consul；即优先\
  级 consul > nacos。

Code optimizations
------------------

- 删除 .conf 示例中的无用配置 wxbot。
- 优化从本地 .conf 获取配置的逻辑，也提供更清晰明确的报错信息。
- tox 重新添加了 windows 场景。
- 更新 CI 工具版本。

<hr>

AyugeSpiderTools 3.5.1 (2023-09-28)
===================================

Bug fixes
---------

- 修复在 `py 3.11` 及以上版本的 `mongo` 相关场景的报错。(:issue:`11`)

Code optimizations
------------------

- 优化 AyuItem 实现，增强可读性及用户输入体验，比如 add_field 增加 IDE 参数提示功能。
- 更新文档中 AyuItem 的使用建议及对应测试。
- 更新测试文件，比如 test_crawl 及 spider 相关方法。

<hr>

AyugeSpiderTools 3.5.0 (2023-09-21)
===================================

Code optimizations
------------------

- scrapy 依赖升级为 2.11.0。
- 统一运行统计的方法，修改运行 stats 中有关时间的获取和计算方法。
- 添加 pre-commit 工具和 CI，提升 commit 和 pull request 体验。
- 更新 readthedocs 的新配置。
- 优化 test_crawl 的测试方法。

<hr>

AyugeSpiderTools 3.4.2 (2023-09-15)
===================================

Bug fixes
---------

- 修复 crawl 模板文件中 TableEnum 的导入问题。
- 修改文档中 kafka 推送示例 typo 问题。

Code optimizations
------------------

- 优化文件下载本地的逻辑，处理当 file_url 不存在时的情况。
- 优化 items，typevar 等模块的 type hint，并删除无用的类型内容。
- 设置包源的优先级。
- 增加测试用例。
- 添加 mypy 工具。

<hr/>

AyugeSpiderTools 3.4.1 (2023-09-07)
===================================

Bug fixes
---------

- 解决 Twisted 版本更新到 23.8.0 不兼容的问题。(:issue:`10`)

Code optimizations
------------------

- scrapy 依赖版本更新为 2.10.1。

<hr/>

AyugeSpiderTools 3.4.0 (2023-08-10)
===================================

Bug fixes
---------

- aiohttp 超时参数由 AIOHTTP_CONFIG 中的 timeout 获取改为直接从 DOWNLOAD_TIMEOUT 中获取。解决在 \
  aiohttp 超时参数值大于 DOWNLOAD_TIMEOUT 时，与程序整体超时设置冲突，考虑程序的整体性，而不去根据 \
  aiohttp 的超时设置来更新项目的整体设置。

Code optimizations
------------------

- aiohttp 添加 allow_redirects 配置参数 ，优化对应文档示例。
- 更新 scrapy 依赖版本为 2.10.0。
- 解决部分 typo 及注解问题。

<hr/>

AyugeSpiderTools 3.3.3 (2023-08-03)
===================================

Bug fixes
---------

- 修复解析 yaml 格式数据依赖缺失的问题。(:issue:`9`)

Code optimizations
------------------

- 本库中解决 Mysql 的 Unknown column 'xx' in 'field list' 部分代码变动，比如不再根据 item 字段\
  是crawl_time 类型格式来给其默认字段格式 DATE，因为用户可能只是存储字段是这个名称，意义并不同，或者它\
  存的是个时间戳等情况。这样需要考虑的问题太复杂了，且具有隐患，不如优先解决字段缺失问题，后续按需再手动\
  调整表字段类型。

<hr/>

AyugeSpiderTools 3.3.2 (2023-07-26)
===================================

New features
------------

- 增加贝塞尔曲线生成轨迹的示例方法。

Code optimizations
------------------

- 将项目中有关文件的操作统一改为 pathlib 的方式。
- 根据 consul 获取配置的方式添加缓存处理，不用每次运行都多次调用同样参数来获取配置。减少请求次数，提高\
  运行效率。
- 更新 README.md 内容，增加对应英文版本。

<hr/>

AyugeSpiderTools 3.3.1 (2023-06-29)
===================================

Code optimizations
------------------

- 优化 item 使用体验，完善功能及对应文档内容，具体请查看 readthedocs item 部分。

<hr/>

AyugeSpiderTools 3.3.0 (2023-06-21)
===================================

Deprecation removals
--------------------

- 优化了 `Item` 体验，升级为 `AyuItem`，使用更方便，但注意与旧版本写法并不兼容：

  - 删除了 `MysqlDataItem` 实现。
  - 删除了 `MongoDataItem` 实现。
  - 增加了 `AyuItem` 参数以方便开发和简化 `pipelines` 结构，新示例请查看 `DemoSpider` 项目或 `readthedocs` 文档对应内容。

New features
------------

- 添加文件下载的示例，具体案例请查看 DemoSpider 中的 demo_file 项目。

Code optimizations
------------------

- 升级依赖库中 numpy 和 loguru 版本，避免其漏洞警告提示。
- 更新对应的模板生成示例，简化一些不常用的配置即注释等。

<hr/>

AyugeSpiderTools 3.2.0 (2023-06-07)
===================================

Deprecation removals
--------------------

- 去除数据表前缀和集合前缀的鸡肋功能：

  - 删除了 MYSQL_TABLE_PREFIX 参数。
  - 删除了 MONGODB_COLLECTION_PREFIX 参数。
- 删除其它的鸡肋功能：

  - 移除 runjs 方便运行 js 方法的鸡肋封装。
  - 移除 rpa 管理自动化程序的方法。
- 删除了使用 requests 作为 scrapy 请求库的功能，推荐使用本库中 aiohttp 的方式。

New features
------------

- 添加 kafka 推送的示例，具体案例请查看 DemoSpider 项目的 demo_kafka 部分。

Code optimizations
------------------

- 增加 RabbitMQ 中 heartbeat 和 socket_timeout 参数可自定义的功能。
- 整理依赖文件。

<hr/>

AyugeSpiderTools 3.1.0 (2023-05-30)
===================================

New features
------------

- 添加 mq 推送的示例，具体案例请查看 DemoSpider 项目的 demo_mq 部分。

Code optimizations
------------------

- 修复部分 typo 问题。

<hr/>

AyugeSpiderTools 3.0.1 (2023-05-17)
===================================

这是一个 major 版本更新，含有 bug 修复、代码优化等。

Deprecation removals
--------------------

- 删除 ayugespidertools 的 cli 名称 -> 改为 ayuge 来管理。

New features
------------

- 修改 item 实现方式，不再通过将字段都存入 alldata 中即可实现动态设置字段的功能，使用更清晰，且能更方便、
  地使用 ItemLoaders 的功能，具体案例请查看 DemoSpider 项目。

Bug fixes
---------

- 修复不会创建表注释的问题。

Code optimizations
------------------

- 修改 dict_keys_to_lower 和 dict_keys_to_upper 的将字典 key 转为大写或小写的功能优化为嵌套字典中\
  所有 key 都转为大写或小写。
- 将模板中 settings.py 中的配置读取放入库中 update_settings 实现，简化 settings.py 文件内容。
- 优化 Makefile 功能，简化清理 __pycache__ 文件夹的功能。
- 修改部分 typo 问题。
- 更新 readthedocs 内容，更新测试文件。

<hr/>

AyugeSpiderTools 2.1.0 (2023-05-09)
===================================

这是一个主要更改了 scrapy 依赖库为 2.9.0 版本，含有 bug 修复。

Deprecation removals
--------------------

- tox 去除 windows 平台的测试场景。

Deprecations
------------

- 下一大版本将删除 ayugespidertools 的 cli 名称 -> 改为 ayuge 来管理。

New features
------------

- 本库依赖库 scrapy 版本升级为 2.9.0。

Bug fixes
---------

- 修复使用 ayuge 及 ayuge -h 命令时，未显示当前库版本的问题。

AyugeSpiderTools 2.0.3 (2023-05-06)
===================================

Deprecations
============

- 下一大版本将删除 ayugespidertools 的 cl` 名称 -> 改为 ayuge 来管理。

New features
------------

- 添加 mongodb 的 asyncio 的示例。

Code optimizations
------------------

- readthedocs 的 markdown 解析由 recommonmark 改为 myst-parser，以支持更多的 markdown 语法。

<hr/>

AyugeSpiderTools 2.0.1 (2023-04-27)
===================================

Deprecation removals
--------------------

- 一些 api 变动：

.. csv-table::
   :header: "更改前", "更改后", "受影响的部分"
   :widths: 15, 15, 25

   "from ayugespidertools.AyugeSpider import AyuSpider", "from ayugespidertools.spiders import AyuSpider", "_"
   "from ayugespidertools.AyuRequest import AioFormRequest", "from ayugespidertools.request import AiohttpFormRequest", "_"
   "from ayugespidertools.AyuRequest import AiohttpRequest", "from ayugespidertools.request import AiohttpRequest", "_"
   "from ayugespidertools.common.Utils import * ", "from ayugespidertools.common.utils import *", "_"
   "from ayugespidertools.Items import * ", "from ayugespidertools.items import *", "_"
   "from <DemoSpider>.common.DataEnum import TableEnum", "from <DemoSpider>.items import TableEnum", "_"
   "from ayugespidertools.AyugeCrawlSpider import AyuCrawlSpider", "from ayugespidertools.spiders import AyuCrawlSpider", "_"
   "ayugespidertools.Pipelines", "ayugespidertools.pipelines", "pipelines"
   "ayugespidertools.Middlewares", "ayugespidertools.middlewares", "middlweares"

- 一些参数配置变动：

.. csv-table::
   :header: "更改前", "更改后", "备注"
   :widths: 10, 15, 30

   "PROXY_URL", "proxy", "代理 proxy 参数"
   "PROXY_INDEX", "index", "代理配置等"

- 一些使用方法更改：

  - 使用 AiohttpRequest 构造请求时，由之前的 meta 中的 aiohttp_args 配置参数，改为由 args 的新增\
    参数取代，其参数类型同样为 dict，也可以为 AiohttpRequestArgs 类型，更容易输入。

Deprecations
------------

- 下一大版本将删除 ayugespidertools 的 cli 名称 -> 改为 ayuge 来管理。

New features
------------

- 丰富 aiohttp 请求场景，增加重试，代理，ssl 等功能。

Code optimizations
------------------

- 更新测试用例。

<hr/>

AyugeSpiderTools 1.1.9 (2023-04-20)
===================================

New features
------------

- 增加 ayuge startproject 命令支持 project_dir 参数。

.. code:: bash

   # 这将在 project dir 目录下创建一个 Scrapy 项目。如果未指定 project dir，则 project dir 将与 myproject 相同。
   ayuge startproject myproject [project_dir]

Bug fixes
---------

- 修复模板中 settings 的 CONSUL 配置信息没有更新为 v1.1.6 版本推荐的使用方法的问题。
- 修复在 startproject 创建项目时生成的 run.sh 中的路径信息错误问题。

Code optimizations
------------------

- 添加测试用例。
- 以后的版本发布说明都会在 ayugespidertools readthedocs 上展示。
