# Release notes

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
