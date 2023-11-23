# Release notes

## AyugeSpiderTools 3.7.0 (2023-11-23)

### Deprecations

- 获取 `nacos` 和 `consul` 中的配置时不再转小写，请按照 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/intro/examples.html) 示例填写。
- 删除 `html2text` 相关依赖及代码，此场景更适合自行实现。
- 安装不再包含非核心依赖，可通过 `pip install ayugespidertools[all]` 安装全部依赖。
- 一些 `api`变动：

  | 更改前                                   | 更改后                                     | 受影响的部分                                                 | 备注                     |
  | ---------------------------------------- | ------------------------------------------ | ------------------------------------------------------------ | ------------------------ |
  | extract_html_to_md                       | 删除                                       | ayugespidertools.formatdata                                  |                          |
  | AliOssBase                               | 转移到 ayugespider.extras 中               | ayugespidertools.oss                                         |                          |
  | yidungap, imgoperation, verificationcode | 转移到 ayugespider.extras 中，并整理在一起 | ayugespidertools.imgoperation<br>ayugespidertools.verificationcode<br>ayugespidertools.common.yidungap | 在 extras 部分查看变化。 |

- 以下是对 `extras` 相关模块所影响较大部分的介绍：

  | 更改前                 | 更改后                         | 受影响的部分                      | 备注 |
  | ---------------------- | ------------------------------ | --------------------------------- | ---- |
  | YiDunGetGap.discern    | CvnpilKit.discern_gap          | ayugespidertools.common.yidungap  |      |
  | Picture.identify_gap   | CvnpilKit.identify_gap         | ayugespidertools.imgoperation     |      |
  | match_img_get_distance | CvnpilKit.match_gap            | ayugespidertools.verificationcode |      |
  | get_normal_track       | CvnpilKit.get_normal_track     | ayugespidertools.verificationcode |      |
  | get_selenium_tracks    | ToolsForAyu.get_selenium_track | ayugespidertools.verificationcode |      |

注意：

- **此变更包含不兼容部分，如果你只使用其中 `scrapy` 扩展库部分，那么除了 `nacos`，`consul` 的 `yaml` 和 `hcl` 解析外对你无影响。**
- **再次提醒，使用时请做好依赖管理，以免不兼容部分对你的影响！**

### New features

- `mongo` 场景添加 `authMechanisem` 配置选项，为可选配置，默认为 `SCRAM-SHA-1`。
- 将 `numpy`, `oss`, `pillow` 等非核心依赖改为可选项，可通过 `pip install ayugespidertools[all]` 安装所有依赖。

### Bug fixes

- 无。

### Code optimizations

- 优化 `aiohttp`, `cvnpil` 等测试用例，将图像相关功能整理并放入 `cvnpil` 模块中。
- `ayuge version` 修改为从 `__version__` 获取信息的方式。
- 更新模板，`mysql_engine` 的示例改为通过 `sqlalchemy` 的方式，减少依赖数且大部分场景运行效率更好。
- 将可选装依赖的相关的功能代码统一放入 `extras` 中，更易管理。

<hr>

## AyugeSpiderTools 3.6.1 (2023-11-06)

### New features

- 无。

### Bug fixes

- 解决 `mq` 推送场景时 `yield AyuItem` 时的错误，现可支持多种格式。
- 解决 `VIT_DIR` 默认参数未存储至 `settings` 中的问题。

### Code optimizations

- 文件下载场景添加 `FILES_STORE` 路径不存在时的自动创建处理。
- `settings` 模板删除无关配置。
- 项目添加 `question issues template`。

<hr>

## AyugeSpiderTools 3.6.0 (2023-10-31)

### Deprecations

- 一些 `api` 变动：

| 更改前                                                       | 更改后                                                       | 受影响的部分          | 备注 |
| ------------------------------------------------------------ | ------------------------------------------------------------ | --------------------- | ---- |
| 删除 `LOGURU_CONFIG` 配置参数                                | 现只需配置 `LOGURU_ENABLED` 即可                             | `slog` 日志模块       |      |
| 删除 `spider` 中 `settings_type` 参数                        | 此为过度设计，若需要可自定义配置                             | 项目配置信息          |      |
| 删除 `spider` 中 `mysql_engine_enabled` 参数                 | 转移到设置中，名称为 `MYSQL_ENGINE_ENABLED`                  | 配置模块，影响较大。  |      |
| `AyuItem` 中 `_table` 参数类型修改<br>删除 `spider` 中 `custom_table_enum` 参数 | 修改为与普通字段一样的 `DataItem` 或 `str` 类型，删除 `demand_code` 字段。 | `spider`，`Item` 模块 |      |
| 删除 `RECORD_LOG_TO_MYSQL` 配置参数                          | 改为 `ayugespidertools.pipelines.AyuStatisticsMysqlPipeline` 方式调用。 | 配置模块              |      |

注意：**此变更包含不兼容内容，请修改不兼容部分并调试正常后再投入生产；本项目在有一些不兼容变更时，会发布 `Minor` 及以上的版本包，请做好依赖版本管理。**

### New features

- 无。

### Bug fixes

- 无。

### Code optimizations

- 设置 `VIT_DIR` 默认参数。
- 去除冗余配置，统一配置风格。将一些过于复杂的模块拆分，便于管理。

<hr>

## AyugeSpiderTools 3.5.2 (2023-10-17)

### New features

- 添加从 `nacos` 中获取配置的方法，若 `.conf` 中同时存在 `consul` 和 `nacos` 配置则优先使用 `consul`；即优先级 `consul` > `nacos`。

### Bug fixes

- 无

### Code optimizations

- 删除 `.conf` 示例中的无用配置 `wxbot`。
- 优化从本地 `.conf` 获取配置的逻辑，也提供更清晰明确的报错信息。
- `tox` 重新添加了 `windows` 场景。
- 更新 `CI` 工具版本。

<hr>

## AyugeSpiderTools 3.5.1 (2023-09-28)

### Bug fixes

- 修复在 `py 3.11` 及以上版本的 `mongo` 相关场景的报错。([issue 11](https://github.com/shengchenyang/AyugeSpiderTools/issues/11))

### Code optimizations

- 优化 `AyuItem` 实现，增强可读性及用户输入体验，比如 `add_field` 增加 `IDE` 参数提示功能。
- 更新文档中 `AyuItem` 的使用建议及对应测试。
- 更新测试文件，比如 `test_crawl` 及 `spider` 相关方法。

<hr>

## AyugeSpiderTools 3.5.0 (2023-09-21)

### Bug fixes

- 无。

### Code optimizations

- `scrapy` 依赖升级为 `2.11.0`。
- 统一运行统计的方法，修改运行 `stats` 中有关时间的获取和计算方法。
- 添加 `pre-commit` 工具和 `CI`，提升 `commit` 和 `pull request` 体验。
- 更新 `readthedocs` 的新配置。
- 优化 `test_crawl` 的测试方法。

<hr>

## AyugeSpiderTools 3.4.2 (2023-09-15)

### Bug fixes

- 修复 `crawl` 模板文件中 `TableEnum` 的导入问题。
- 修改文档中 `kafka` 推送示例 `typo` 问题。

### Code optimizations

- 优化文件下载本地的逻辑，处理当 `file_url` 不存在时的情况。
- 优化 `items`，`typevar` 等模块的 `type hint`，并删除无用的类型内容。
- 设置包源的优先级。
- 增加测试用例。
- 添加 `mypy` 工具。

<hr/>

## AyugeSpiderTools 3.4.1 (2023-09-07)

### Bug fixes

- 解决 `Twisted` 版本更新到 `23.8.0` 不兼容的问题。([issue 10](https://github.com/shengchenyang/AyugeSpiderTools/issues/10))

### Code optimizations

- `scrapy` 依赖版本更新为 `2.10.1`。

<hr/>

## AyugeSpiderTools 3.4.0 (2023-08-10)

### Deprecation removals

- 无。

### Deprecations

- 无。

### New features

- 无。

### Bug fixes

- `aiohttp` 超时参数由 `AIOHTTP_CONFIG` 中的 `timeout` 获取改为直接从 `DOWNLOAD_TIMEOUT` 中获取。解决在 `aiohttp` 超时参数值大于 `DOWNLOAD_TIMEOUT` 时，与程序整体超时设置冲突，考虑程序的整体性，而不去根据 `aiohttp` 的超时设置来更新项目的整体设置。

### Code optimizations

- `aiohttp` 添加 `allow_redirects` 配置参数 ，优化对应文档示例。
- 更新 `scrapy` 依赖版本为 `2.10.0`。
- 解决部分 `typo` 及注解问题。

<hr/>

## AyugeSpiderTools 3.3.3 (2023-08-03)

### Deprecation removals

- 无。

### Deprecations

- 无。

### New features

- 无。

### Bug fixes

- 修复解析 `yaml` 格式数据依赖缺失的问题。（[issue 9](https://github.com/shengchenyang/AyugeSpiderTools/issues/9)）

### Code optimizations

- 本库中解决 `Mysql` 的 `Unknown column 'xx' in 'field list'` 部分代码变动，比如不再根据 `item` 字段是`crawl_time` 类型格式来给其默认字段格式 `DATE`，因为用户可能只是存储字段是这个名称，意义并不同，或者它存的是个时间戳等情况。这样需要考虑的问题太复杂了，且具有隐患，不如优先解决字段缺失问题，后续按需再手动调整表字段类型。

<hr/>

## AyugeSpiderTools 3.3.2 (2023-07-26)

### Deprecation removals

- 无。

### Deprecations

- 无。

### New features

- 增加贝塞尔曲线生成轨迹的示例方法。

### Bug fixes

- 无。

### Code optimizations

- 将项目中有关文件的操作统一改为 `pathlib` 的方式。
- 根据 `consul` 获取配置的方式添加缓存处理，不用每次运行都多次调用同样参数来获取配置。减少请求次数，提高运行效率。
- 更新 `README.md` 内容，增加对应英文版本。

<hr/>

## AyugeSpiderTools 3.3.1 (2023-06-29)

### Deprecation removals

- 无。

### Deprecations

- 无。

### New features

- 无。

### Bug fixes

- 无。

### Code optimizations

- 优化 `item` 使用体验，完善功能及对应文档内容，具体请查看 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/topics/items.html) `item` 部分。

<hr/>

## AyugeSpiderTools 3.3.0 (2023-06-21)

### Deprecation removals

- 优化了 `Item` 体验，升级为 `AyuItem`，使用更方便，但注意与旧版本写法并不兼容：
  - 删除了 `MysqlDataItem` 实现。
  - 删除了 `MongoDataItem` 实现。
  - 增加了 `AyuItem` 参数以方便开发和简化 `pipelines` 结构，新示例请查看 `DemoSpider` 项目或 `readthedocs` 文档对应内容。

### Deprecations

- 无。

### New features

- 添加文件下载的示例，具体内容及示例请查看 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/topics/pipelines.html#mq) 上对应内容，具体案例请查看 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 中的 `demo_file` 项目。

### Bug fixes

- 无。

### Code optimizations

- 升级依赖库中 `numpy` 和 `loguru` 版本，避免其漏洞警告提示。
- 更新对应的模板生成示例，简化一些不常用的配置即注释等。

<hr/>

## AyugeSpiderTools 3.2.0 (2023-06-07)

### Deprecation removals

- 去除数据表前缀和集合前缀的鸡肋功能：
  - 删除了 `MYSQL_TABLE_PREFIX` 参数。
  - 删除了 `MONGODB_COLLECTION_PREFIX` 参数。
- 删除其它的鸡肋功能：
  - 移除 `runjs` 方便运行 `js` 方法的鸡肋封装。
  - 移除 `rpa` 管理自动化程序的方法。
- 删除了使用 `requests` 作为 `scrapy` 请求库的功能，推荐使用本库中 `aiohttp` 的方式。

### Deprecations

- 无。

### New features

- 添加 `kafka` 推送的示例，具体内容及示例请查看 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/topics/pipelines.html#mq) 上对应内容，具体案例请查看 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 项目。

### Bug fixes

- 无。

### Code optimizations

- 增加 `RabbitMQ` 中 `heartbeat` 和 `socket_timeout` 参数可自定义的功能。
- 整理依赖文件。

<hr/>

## AyugeSpiderTools 3.1.0 (2023-05-30)

### Deprecation removals

- 无。

### Deprecations

- 无。

### New features

- 添加 `mq` 推送的示例，具体内容及示例请查看 [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/topics/pipelines.html#mq) 上对应内容，具体案例请查看 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 项目。

### Bug fixes

- 无。

### Code optimizations

- 修复部分 `typo` 问题。

<hr/>

## AyugeSpiderTools 3.0.1 (2023-05-17)

这是一个 `major` 版本更新，含有 `bug` 修复、代码优化等。

### Deprecation removals

- 删除 `ayugespidertools` 的 `cli` 名称 -> 改为 `ayuge` 来管理。

### Deprecations

- 无。

### New features

- 修改 `item` 实现方式，不再通过将字段都存入 `alldata` 中即可实现动态设置字段的功能，使用更清晰，且能更方便地使用 `ItemLoaders` 的功能，具体内容及示例请查看 [readthedocs](https://ayugespidertools.readthedocs.io/en/ayugespidertools-3.0.1/topics/items.html) 上对应内容，具体案例请查看 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 项目。

### Bug fixes

- 修复不会创建表注释的问题。

### Code optimizations

- 修改 `dict_keys_to_lower` 和 `dict_keys_to_upper` 的将字典 key 转为大写或小写的功能优化为嵌套字典中所有 key 都转为大写或小写。
- 将模板中 `settings.py` 中的配置读取放入库中 `update_settings` 实现，简化 `settings.py` 文件内容。
- 优化 `Makefile` 功能，简化清理 `__pycache__` 文件夹的功能。
- 修改部分 `typo` 问题。
- 更新 `readthedocs` 内容，更新测试文件。

<hr/>

## AyugeSpiderTools 2.1.0 (2023-05-09)

这是一个主要更改了 `scrapy` 依赖库为 `2.9.0` 版本，含有 `bug` 修复。

### Deprecation removals

- `tox` 去除 `windows` 平台的测试场景。

### Deprecations

- 下一大版本将删除 `ayugespidertools` 的 `cli` 名称 -> 改为 `ayuge` 来管理。

### New features

- 本库依赖库 `scrapy` 版本升级为 `2.9.0`。

### Bug fixes

- 修复使用 `ayuge` 及 `ayuge -h` 命令时，未显示当前库版本的问题。

### Code optimizations

- 无。

<hr/>

## AyugeSpiderTools 2.0.3 (2023-05-06)

此版本为微小变动。

### Deprecation removals

- 无

### Deprecations

- 下一大版本将删除 `ayugespidertools` 的 `cli` 名称 -> 改为 `ayuge` 来管理。

### New features

- 添加 `mongodb` 的 `asyncio` 的示例。

### Bug fixes

- 无

### Code optimizations

- `readthedocs` 的 `markdown` 解析由 `recommonmark` 改为 `myst-parser`，以支持更多的 `markdown` 语法。

<hr/>

## AyugeSpiderTools 2.0.1 (2023-04-27)

此版本为大版本更新，修改了项目结构以统一本库及与 `scrapy` 结合的代码风格，也有一些功能完善等。最新功能示例请在 [DemoSpider](https://github.com/shengchenyang/DemoSpider/) 或 [readthedocs](https://ayugespidertools.readthedocs.io/en/ayugespidertools-2.0.1/) 中查看。

### Deprecation removals

- 一些 `api` 变动：

| 更改前                                                       | 更改后                                                  | 备注        |
| ------------------------------------------------------------ | ------------------------------------------------------- | ----------- |
| from ayugespidertools.AyugeSpider import AyuSpider           | from ayugespidertools.spiders import AyuSpider          |             |
| from ayugespidertools.AyuRequest import AioFormRequest       | from ayugespidertools.request import AiohttpFormRequest |             |
| from ayugespidertools.AyuRequest import AiohttpRequest       | from ayugespidertools.request import AiohttpRequest     |             |
| from ayugespidertools.common.Utils import *                  | from ayugespidertools.common.utils import *             |             |
| from ayugespidertools.Items import *                         | from ayugespidertools.items import *                    |             |
| from <DemoSpider>.common.DataEnum import TableEnum           | from <DemoSpider>.items import TableEnum                |             |
| from ayugespidertools.AyugeCrawlSpider import AyuCrawlSpider | from ayugespidertools.spiders import AyuCrawlSpider     |             |
| ayugespidertools.Pipelines                                   | ayugespidertools.pipelines                              | pipelines   |
| ayugespidertools.Middlewares                                 | ayugespidertools.middlewares                            | middlweares |

- 一些参数配置变动：

| 更改前      | 更改后 | 备注            |
| ----------- | ------ | --------------- |
| PROXY_URL   | proxy  | 代理 proxy 参数 |
| PROXY_INDEX | index  | 代理配置等      |

注：所有配置的 `key` 都统一改为小写

- 一些使用方法更改：
  - 使用 `AiohttpRequest` 构造请求时，由之前的 `meta` 中的 `aiohttp_args` 配置参数，改为由 `args` 的新增参数取代，其参数类型同样为 `dict`，也可以为 `AiohttpRequestArgs` 类型，更容易输入。

### Deprecations

- 下一大版本将删除 `ayugespidertools` 的 `cli` 名称 -> 改为 `ayuge` 来管理。

### New features

- 丰富 `aiohttp` 请求场景，增加重试，代理，`ssl` 等功能。


### Bug fixes

- 无

### Code optimizations

- 更新测试用例。

<hr/>

## AyugeSpiderTools 1.1.9 (2023-04-20)

这是一个维护版本，具有次要功能、错误修复和清理。

### Deprecation removals

- 无

### Deprecations

- 无

### New features

- 增加 `ayuge startproject` 命令支持 `project_dir` 参数。

  ```shell
  # 这将在 project dir 目录下创建一个 Scrapy 项目。如果未指定 project dir，则 project dir 将与 myproject 相同。
  ayuge startproject myproject [project_dir]
  ```

### Bug fixes

- 修复模板中 `settings` 的 `CONSUL` 配置信息没有更新为 `v1.1.6` 版本推荐的使用方法的问题。([releases ayugespidertools-1.1.6](https://github.com/shengchenyang/AyugeSpiderTools/releases/tag/ayugespidertools-1.1.6))
- 修复在 `startproject` 创建项目时生成的 `run.sh` 中的路径信息错误问题。

### Code optimizations

- 添加测试用例。
- 以后的版本发布说明都会在 [ayugespidertools readthedocs](https://ayugespidertools.readthedocs.io/en/latest/additional/news.html) 上展示。
