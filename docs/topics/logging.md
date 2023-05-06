# Logging

`Scrapy` 用 [`logging`](https://docs.python.org/3/library/logging.html#module-logging) 来记录日志，日志记录开箱即用，并且可以在某种程度上使用[日志设置](https://docs.scrapy.org/en/latest/topics/logging.html#topics-logging-settings)中列出的 `Scrapy` 设置进行配置。

本文不再介绍其详细配置及用法，请移步其官网文档中查看。`AyugeSpiderTools` 库会在 `settings` 中默认设置一个日志存储配置，默认放在项目的 `logs` 文件夹下，其名称为项目名称，如下所示：

```python
# 日志管理
LOG_FILE = f"{LOG_DIR}/DemoSpider.log"

# 配置中 DemoSpider 是与 ayugespidertools startproject <project_name> 中的项目名称对应的
```

## slog 日志

`ayugespidertools` 添加了 `loguru` 库来管理日志，可以很方便的查看不同日志等级的信息。可以在 `spider` 脚本中使用 `spider.slog` 或 `self.slog` 即可记录日志。同样，本库会在 `settings` 中也默认设置一个 `loguru` 的日志存储配置，也放在项目的 `logs` 文件夹下，如下所示：

```python
# 本库只会持久化记录 error 级别的日志，但在调试时也可以方便地查看（包括其它等级的）控制台日志
logger.add(
    env.str("LOG_ERROR_FILE", f"{LOG_DIR}/error.log"),
    level="ERROR",
    rotation="1 week",
    retention="7 days",
    enqueue=True,
)
```

## 日志级别

`ayugespidertools` 中的 `loguru` 日志等级与 `Python` 的内置日志记录定义一致，大致分为 5 个不同的级别来指示给定日志消息的严重性。以下是标准的，按降序排列：

1. `slog.CRITICAL`- 对于严重错误（最高严重性）
2. `slog.ERROR`- 对于常规错误
3. `slog.WARNING`- 警告信息
4. `slog.INFO`- 用于信息性消息
5. `slog.DEBUG`- 用于调试消息（最低严重性）

## 如何记录消息

至于如何使用 `scrapy logging` 来记录的示例就不再展示了，具体使用方法请看文档： [scrapy logging 使用说明](https://docs.scrapy.org/en/latest/topics/logging.html)，本库更推荐在调试阶段使用 `loguru` 来打印日志，会更快捷和明显地查看自己注意的部分。

`ayugespidertools` 会在 `startproject` 后默认再 `settings` 中添加一个日志配置，用于当前项目全局使用，可以在项目的各个目录文件中使用。

以下是如何使用`loguru` 的`WARNING` 级别记录消息的快速示例：

```python
# project_name 为当前所在的 scrapy 项目名称
from <project_name>.settings import logger
logger.warning("This is a warning")
```

因为 `Loguru` 的理念是：**只有一个 [`logger`](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger)**。将日志消息分派给已配置处理程序的对象。`Logger` 是 `loguru` 的核心对象，每个日志配置和使用都要通过对其中一个方法的调用。只有一个记录器，因此在使用之前不需要检索一个记录器。具体请查看文档：[loguru 使用说明](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger)

所以，你也可以直接使用如下方式，也会在全局中使用同一个 `loguru`。

```python
from loguru import logger

logger.info("this is a info log")
```

## 从 spider 记录

```python
import ayugespidertools


class MySpider(ayugespidertools.AyuSpider):

    name = 'myspider'
    start_urls = ['https://scrapy.org']

    def parse(self, response):
        # 此条（error 级别以下的）日志默认下只会在控制台输出
        self.slog.info(f"info: Parse function called on {response.url}")
        # 此条日志在默认下会持久化存储至 error.log 中
        self.slog.error(f"error: Parse function called on {response.url}")
```
