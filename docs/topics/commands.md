# 命令行工具

`AyugeSpiderTools` 是直接使用 `scrapy` 命令行工具来控制的，这里简称为 `AyugeSpiderTools工具`，以区别于我们简称为“命令”或“Scrapy命令”的子命令。

`AyugeSpiderTools` 工具只提供了常用的几个命令，用于多种用途，每个命令都接受一组不同的参数和选项。但是，其它缺失的命令你可以直接使用 `Scrapy` 的即可。

## 配置设置

未改变，也是在在标准位置的 `ini` 样式文件中查找配置参数`scrapy.cfg`：

这些文件中的设置按列出的优先顺序合并：用户定义的值比系统范围的默认值具有更高的优先级，并且项目范围的设置将在定义时覆盖所有其他设置。

## AyugeSpiderTools 项目的默认结构

在深入研究命令行工具及其子命令之前，让我们先了解一下项目的目录结构。

虽然可以修改，但是所有的项目默认都有相同的文件结构，类似这样：

```shell
|-- DemoSpider
|   |-- common
|   |   `-- DataEnum.py
|   |-- __init__.py
|   |-- items.py
|   |-- logs
|   |   |-- DemoSpider.log
|   |   `-- error.log
|   |-- middlewares.py
|   |-- pipelines.py
|   |-- run.py
|   |-- run.sh
|   |-- settings.py
|   |-- spiders
|   |   |-- __init__.py
|   |   `-- spider1.py
|   `-- VIT
|       `-- 请修改.conf中的配置信息
|-- .gitignore
|-- pyproject.toml
|-- README.md
|-- requirements.txt
`-- scrapy.cfg
```

文件所在的目录 `scrapy.cfg` 称为*项目根目录*。该文件包含定义项目设置的 `python` 模块的名称。这是一个例子：

```shell
[settings]
default = DemoSpider.settings
```

## 使用 AyugespiderTools 工具

您可以先运行不带参数的 `AyugeSpiderTools` 工具，它会打印一些使用帮助和可用的命令：

```shell
AyugeSpiderTools None - no active project

Usage:
  ayugespidertools <command> [options] [args]

Available commands:
  genspider     Generate new spider using pre-defined templates
  startproject  Create new project
  version       Print AyugeSpiderTools version

  [ more ]      More commands available when run from project directory

Use "ayugespidertools <command> -h" to see more info about a command
```

### 创建项目

您通常使用该工具做的第一件事是创建您的项目：

```shell
ayugespidertools startproject myproject [project_dir]
```

这将在该目录下创建一个 `Scrapy` 项目 `project_dir`。如果 `project_dir` 未指定，则项目目录将与 `myproject` 相同。

接下来，进入新项目目录：

```shell
cd project_dir
```

您已准备好使用该命令从那里管理和控制您的项目。

### 控制项目

您可以使用项目内部的工具来控制和管理它们。

例如，要创建一个新的蜘蛛：

```shell
ayugespidertools genspider mydomain mydomain.com
```

## 启动项目

- 句法：`ayugespidertools startproject <project_name> [project_dir]`
- 需要项目：*无*

在 `project dir` 目录下创建一个名为 `project_name` 的新项目。如果未指定项目目录，则项目目录将与项目名称相同。

使用示例：

```shell
ayugespidertools startproject myproject
```

## 可用的工具命令

本节包含可用内置命令的列表以及说明和一些用法示例。请记住，您始终可以通过运行以下命令获取有关每个命令的更多信息：

```shell
ayugespidertools <command> -h
```

您可以使用以下命令查看所有可用命令：

```shell
ayugespidertools -h
```

### 启动项目

- 句法：`ayugespidertools startproject <project_name> [project_dir]`
- 需要项目：*无*

在 `project dir` 目录下创建一个名为 `project name` 的新项目。如果未指定项目目录，则项目目录将与项目名称相同。

使用示例：

```shell
ayugespidertools startproject myproject
```

### genspider

- 句法：`ayugespidertools genspider [-t template] <name> <domain or URL>`
- 需要项目：*无*

使用示例：

```shell
$ ayugespidertools genspider -l
Available templates:
  async
  basic
  crawl
  csvfeed
  xmlfeed

$ ayugespidertools genspider example example.com
Created spider 'example' using template 'basic'

$ ayugespidertools genspider -t crawl scrapyorg scrapy.org
Created spider 'scrapyorg' using template 'crawl'
```