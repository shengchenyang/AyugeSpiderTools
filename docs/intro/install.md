# 安装指南

## 支持的 Python 版本

`AyugeSpiderTools` 需要 `Python 3.8.1+`。

## 安装 AyugeSpiderTools

为了向您展示 `ayugespidertools` 带来了什么，我们将带您通过一个 `Scrapy Spider` 示例，使用最简单的方式来运行蜘蛛。

> 可以使用以下命令从 `PyPI` 安装 `ayugespidertools` 及其依赖项：

1. 若你的数据库场景只需要 `mysql` 和 `mongodb`，且不需要本库中的扩展功能，那么直接简洁安装即可，命令如下：

```shell
pip install ayugespidertools
```

2. 若你的数据库场景需要本库中的其他扩展，且同样不需要本库中的扩展功能，那么安装数据库版本最好，命令如下：

> 可选1：通过以下命令安装所有包含所有数据库依赖：

```shell
pip install ayugespidertools[database]
```

3. 全部依赖安装命令如下：

> 可选2：通过以下命令安装所有依赖：

```shell
pip install ayugespidertools[all]
```

注意：若你只需要 `scrapy` 扩展库的简单功能，那么默认的简洁依赖安装即可；一些可选择的开发功能（都会放在 `extras` 部分）若要使用，请使用完整安装。

强烈建议您将 `ayugespidertools` 安装在专用的 `virtualenv` 中，以避免与您的系统包发生冲突。

### 值得知道的事情

`ayugespidertools` 是依赖于 `Scrapy` 开发的，对其在爬虫开发中遇到的常用操作进行扩展。

### 使用虚拟环境（推荐）

建议在所有平台上的虚拟环境中安装此库。

有关如何创建虚拟环境的信息，请参阅[虚拟环境和包](https://docs.python.org/3/tutorial/venv.html#tut-venv)。
