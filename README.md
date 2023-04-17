![ayugespidertools-logo](https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/main/artwork/ayugespidertools-logo.png)

[![OSCS Status](https://www.oscs1024.com/platform/badge/AyugeSpiderTools.svg?size=small)](https://www.murphysec.com/accept?code=0ec375759aebea7fd260248910b98806&type=1&from=2)
![GitHub](https://img.shields.io/github/license/shengchenyang/AyugeSpiderTools)
![python](https://img.shields.io/badge/python-3.8.1%2B-blue)
![GitHub Workflow Status (with branch)](https://img.shields.io/github/actions/workflow/status/shengchenyang/AyugeSpiderTools/codeql.yml?branch=main)
![Read the Docs](https://img.shields.io/readthedocs/ayugespidertools)
![GitHub all releases](https://img.shields.io/github/downloads/shengchenyang/AyugeSpiderTools/total?label=releases%20downloads)
![PyPI - Downloads](https://img.shields.io/pypi/dm/AyugeSpiderTools?label=pypi%20downloads)

# AyugeSpiderTools 工具说明

> 一句话介绍：用于扩展 `Scrapy` 功能来解放双手，还内置一些爬虫开发中的通用方法。

## 前言

在使用 `Python` `Scrapy` 库开发爬虫时，免不了会重复的修改和编写 `settings.py`，`middlewares.py`，`pipelines.py`，`item.py` 和一些通用方法或脚本，但其实各个项目中的这些文件内容大致相同，那为何不把他们统一整理在一起呢。虽说可以使用 `scrapy` 的模板功能，但还是无法适配所有的开发场景。

刚开始我也只是想把它用来适配 `Mysql` 存储的场景，可以自动创建相关数据库，数据表，字段注释，自动添加新添加的字段，和自动修复常见（字段编码，`Data too long`，存储字段不存在等等）的存储问题。后来不断优化和添加各种场景，使得爬虫开发在通用场景下几乎只用在意 `spider` 脚本的解析规则和 `VIT` 下的 `.conf` 配置即可，脱离无意义的重复操作。

至于此库做了哪些功能，只要你熟悉 `python` 语法和 `scrapy` 库，再结合 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 中的应用示例，你可以很快上手。具体的内容和注意事项也可以在 [AyugeSpiderTools readthedocs 文档](https://ayugespidertools.readthedocs.io/en/latest/) 中查看。

## 1. 前提条件

> `python 3.8+` 可以直接输入以下命令：

```shell
pip install ayugespidertools -i https://pypi.org/simple
```

注：本库依赖中的 `pymongo` 版本要在 `^3.12.3` (即`3.13.0` 及以下) 是因为我的 `mongoDB` 的版本为 `3.4`，`pymogo` 官方从 `3.13.0` 以后的版本开始不再支持 `3.6` 版本以下的 `MongoDB` 数据库了，望周知！**你也可以根据 [3.3](#3.3.-Build-Your-Own-Library) 自定义库**

## 2. 使用方法

> 项目主要包含两部分：
>

- 开发场景中的工具库
  - 比如 `MongoDB`，`Mysql sql` 语句的生成，图像处理，数据处理相关 ... ...
- `Scrapy` 扩展功能（**主推功能 — 解放双手**）
  - 使爬虫开发无须在意数据库和数据表结构，不用去管常规 `item, pipelines` 和 `middlewares` 的文件的编写。内置通用的 `middlewares` 中间件方法（随机请求头，动态/独享代理等），和常用的 `pipelines` 方法（`Mysql`，`MongoDB` 存储，`Kafka`，`RabbitMQ` 推送队列等）。

### 2.1. Scrapy 扩展库场景

> 开发人员只需根据命令生成示例模板，再配置并激活相关设置即可，可以专注于爬虫 `spider` 的开发。

使用方法示例 `GIF` 如下：

![ayugespidertools.gif](https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/main/examples/ayugespidertools-use.gif)

对以上 `GIF` 中的步骤进行解释：

```shell
# 注：ayugespidertools cli 的名称也可用 ayuge 来代替，输入体验更友好。

# 查看库版本
ayugespidertools version

# 创建项目
ayugespidertools startproject <project_name>

# 进入项目根目录
cd <project_name>

# 生成爬虫脚本
ayugespidertools genspider <spider_name> <example.com>

# 替换(覆盖)为真实的配置 .conf 文件；
# 这里是为了演示方便，正常情况是直接在 VIT 路径下的 .conf 配置文件填上相关配置即可
cp /root/mytemp/.conf DemoSpider/VIT/.conf

# 运行脚本
scrapy crawl <spider_name>
```

具体使用方法请在 [DemoSpider 之 AyugeSpiderTools 工具应用示例](https://github.com/shengchenyang/DemoSpider) 项目中查看，目前已适配以下场景：

```diff
# 采集数据存入 `Mysql` 的场景：
- 1).demo_one: 配置根据本地 `settings` 的 `LOCAL_MYSQL_CONFIG` 中取值
+ 3).demo_three: 配置根据 `consul` 的应用管理中心中取值
+ 5).demo_five: 异步存入 `Mysql` 的场景

# 采集数据存入 `MongoDB` 的场景：
- 2).demo_two: 采集数据存入 `MongoDB` 的场景（配置根据本地 `settings` 的 `LOCAL_MONGODB_CONFIG` 中取值）
+ 4).demo_four: 采集数据存入 `MongoDB` 的场景（配置根据 `consul` 的应用管理中心中取值）
+ 6).demo_six: 异步存入 `MongoDB` 的场景

# 将 `Scrapy` 的 `Request`，`FormRequest` 替换为其它工具实现的场景
- 以上为使用 scrapy Request 的场景
+ 7).demo_seven: scrapy Request 替换为 requests 请求的场景(一般情况下不推荐使用，同步库
+ 会拖慢 scrapy 速度，可用于测试场景)

+ 8).demo_eight: 同时存入 Mysql 和 MongoDB 的场景

- 9).demo_aiohttp_example: scrapy Request 替换为 aiohttp 请求的场景，提供了各种请求场景示例（GET,POST）
+ 10).demo_aiohttp_test: scrapy aiohttp 在具体项目中的使用方法示例

+ 11).demo_proxy_one: 快代理动态隧道代理示例
+ 12).demo_proxy_two: 测试快代理独享代理

+13).demo_AyuTurboMysqlPipeline: mysql 同步连接池的示例
+14).demo_crawl: 支持 scrapy CrawlSpider 的示例

# 本库中给出支持 Item Loaders 特性的示例(文档地址：https://ayugespidertools.readthedocs.io/en/latest/topics/loaders.html)
+15).demo_item_loader: 本库 ScrapyClassicItem 及原生 scrapy item 动态添加 item 字段及支持 Item Loaders 的示例
+16).demo_item_loader_two: 展示本库使用 itemLoader 特性的示例
```

注：具体内容及时效性请以 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 项目中描述为准。

### 2.2. 开发场景

> 这里不再一一列举所有功能，大概介绍下包含的大致功能。

- **数据处理相关:** 比如一些字符串处理，`url` 拼接处理。
- **常用加解密、编码:** `rsa`, `mm3` 等，其实更推荐 [chepy](https://github.com/securisec/chepy) 库 - 你能用 [icyberchef](https://icyberchef.com/) 测试跑通的加解密都可以用此库更方便地实现，两三行代码即可搞定。
- **sql 语句拼接:** 只能做到最简单的逻辑，如果需要灵活或稍复杂的情况，请参考 `directsql`, `python-sql`, `pypika`或 `pymilk` 等其它第三方类似功能库的实现方法。
- **滑块图片缺口位置识别及轨迹生成**

注：

> 滑块缺口识别示例，双缺口也可正常识别。

| 识别结果展示                                                                                                                                                                                | 备注                                                   |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| <img src="https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/main/examples/slider_notch_distance_recognite1.png" alt="slider_notch_distance_recognite1" style="zoom: 25%;" /> | 无                                                     |
| <img src="https://raw.githubusercontent.com/shengchenyang/AyugeSpiderTools/main/examples/slider_notch_distance_recognite2.png" alt="slider_notch_distance_recognite2" style="zoom: 25%;" /> | 可以展示只识别滑块小方块的结果，得到更精准的坐标数据。 |

## 3. 补充

**在使用过程中若遇到各种问题，或有任何优化建议欢迎提 Issues !**

### 3.1. 跑通测试示例

前提：需要在 `tests` 的 `VIT` 目录下创建 `.conf` 文件，已给出示例文件，请填写测试所需内容，然后：

- 可以直接使用 `tox` 来运行测试。

- 本库以 [poetry](https://python-poetry.org/docs/) 开发，那么直接新环境下运行 `poetry install` 后，手动运行目标测试或 `pytest` 命令来测试等皆可。
- 也可以使用 `make` 工具，`make start` 然后 `make test` 即可。

测试完毕后 `make clean` 清理文件。

### 3.2. 你可能在意的事

> 此项目会慢慢丰富 `python` 开发中的遇到的通用方法，详情请见 [TodoList](#TodoList)。

1. 若你觉得某些场景下的功能实现不太符合你的预期，想要修改或添加自定义功能，或移除对你无用模块、修改库名等，你可以自行修改后 `build`。
2. 本库主推 `scrapy` 扩展（即增强版的自定义模板）的功能，在使用本库时，理论上并不会影响你 `scrapy` 项目及其它组件，且你也可以根据上条须知来增强此库功能。因为模板功能天生就有及其明确的优缺点，我无法覆盖所有应用场景，**但是它的高效率的确会解放双手**。

### 3.3. Build-Your-Own-Library

> 具体内容请以 [poetry 官方文档](https://python-poetry.org/docs/) 为准。

据 [3.2](#3.2.-你可能在意的事) 可知，你可以 `clone` 源码后，修改任意方法（比如你的项目场景下可能需要其它的日志配置默认值，或添加其它的项目结构模板等），修改完成后 `poetry  build` 或 `make build` 即可打包使用。

比如你可能需要更新依赖库中 `pymongo` 为新版本 `x.x.x`，那只需 `poetry install` 安装现有依赖后，再 `poetry add pymongo@x.x.x` 安装目标版本（尽量不要使用 `poetry update pymongo`），确定测试正常了即可 `poetry build` 打包使用。

## TodoList

- [x] `scrapy` 的扩展功能场景
  - [x] `scrapy` 脚本运行信息统计和项目依赖表采集量统计，可用于日志记录和预警
  - [x] 自定义模板，在 `ayugespidertools startproject <projname>` 和 `ayugespidertools genspider <spidername>` 时生成适合本库的模板文件
  - [x] ~~增加根据 `nacos` 来获取配置的功能~~ -> 改为增加根据 `consul` 来获取配置的功能
  - [x] 代理中间件（独享代理、动态隧道代理）
  - [x] 随机请求头 `UA` 中间件，根据 `fake_useragent` 中的权重来随机
  - [x] 使用以下工具来替换 `scrapy` 的 `Request` 来发送请求
    - [x] `requests`: 这个不推荐使用，`requests` 同步库会降低 `scrapy` 运行效率
    - [x] `aiohttp`: 集成将 `scrapy Request` 替换为 `aiohttp` 的协程方式
  - [x] `Mysql` 存储的场景下适配
    - [x] 自动创建 `Mysql` 用户场景下需要的数据库和数据表及字段格式，还有字段注释
  - [x] `MongoDB` 存储的场景下适配，编写风格与 `Mysql` 存储等场景下一致
  - [x] `asyncio` 语法支持与 `async` 第三方库支持示例
    - [x] `spider` 中使用 `asyncio` 的 `aiohttp` 示例
    - [x] `pipeline` 中使用 `asyncio` 的 `aioMysql` 示例
  - [ ] 集成 `Kafka`，`RabbitMQ` 等数据推送功能
- [x] 常用开发场景
  - [x] `sql` 语句拼接，只是简单场景，后续优化。已给出优化方向，参考库等信息。
  - [x] `mongoDB` 语句拼接
  - [x] 数据格式化处理，比如：去除网页标签，去除无效空格等
  - [x] 字体反爬还原方法
    - [x] 基于 `ttf`，`woff` 之类的字体文件映射，或结合 `css` 等实现
      - [x] 可以直接在字体文件 `xml` 中找到映射关系的：使用 [fontforge](https://github.com/fontforge/fontforge/releases) 工具导出映射即可。
      - [x] 无法找到映射关系的，则一般使用 `ocr` 识别（准确率非百分百），通过 `fontforge` 导出每个映射的 `png`，后再通过各种方式识别。
  - [x] `html` 格式转 `markdown` 格式
  - [x] `html` 数据处理，去除标签，不可见字符，特殊字符改成正常显示等等等
  - [x] 添加常用的图片验证码中的处理方法
    - [x] 滑块缺口距离的识别方法（多种实现方式）
    - [x] 根据滑块距离生成轨迹数组的方法
    - [x] 识别点选验证码位置及点击顺序，识别结果不太好，待优化
    - [x] 图片乱序混淆的还原方法示例

**注：**

1. 由于 `scrapy` 扩展库的开源项目众多，在使用本库的基础上扩展它们，与使用 `scrapy` 时扩展它们的用法一致，所以不再开发一些其它工具已经拥有且稳定的功能，但也会尽量开发一些常用且通用的方法来提升效率。
2. 字体反爬部分不会给出详细解决示例，不管是使用 `fontforge`，`fontTools` 或 `ocr` 等工具，已经脱离本库的范围了，我会给出部分依赖的方法，但不会添加以上工具库的依赖了，而导致本库依赖过于杂糅。而且，若要实现高可用的字体映射也比较简单，请自行实现，可能会考虑新开 `pypi` 库来实现此部分。
