<p align="center">
    <a href="https://ayugespidertools.readthedocs.io" target="_blank" rel="noopener noreferrer">
        <img src="./artwork/ayugespidertools-logo.png" alt="ayugespidertools-logo">
    </a>
</p>
<hr/>

# AyugeSpiderTools Introduce

[![OSCS Status](https://www.oscs1024.com/platform/badge/AyugeSpiderTools.svg?size=small)](https://www.murphysec.com/accept?code=0ec375759aebea7fd260248910b98806&type=1&from=2)
![GitHub](https://img.shields.io/github/license/shengchenyang/AyugeSpiderTools)
![python](https://img.shields.io/badge/python-3.8.1%2B-blue)
![GitHub Workflow Status (with branch)](https://img.shields.io/github/actions/workflow/status/shengchenyang/AyugeSpiderTools/codeql.yml?branch=main)
![Read the Docs](https://img.shields.io/readthedocs/ayugespidertools)
![GitHub all releases](https://img.shields.io/github/downloads/shengchenyang/AyugeSpiderTools/total?label=releases%20downloads)
![PyPI - Downloads](https://img.shields.io/pypi/dm/AyugeSpiderTools?label=pypi%20downloads)

[简体中文](./README.md) | **English**

## Overview

> One-sentence introduction: Used to extend Scrapy functionality and free up your hands.

When developing a spider using Scrapy, it is inevitable that one has to repeatedly
write `settings`, `items`, `middlewares`, `pipeline`, and some common methods. However, these contents in different
projects are roughly the same. So why not consolidate them together? I also want to extend some functionality, such as
automatically modifying the corresponding `item` and `pipeline` when adding a field in the spider, without even manually
modifying the table structure of MySQL. In this case, the template feature of Scrapy is not enough.

The main idea of the project is to allow developers to focus only on writing spider scripts, reducing development and
maintenance processes. In an ideal state, one only needs to pay attention to the parsing rules of fields in the spider
and the `.conf` configuration under `VIT`, and be free from meaningless repetitive operations.

Taking the scenario of storing data in MySQL as an example, the project can automatically create relevant databases,
data tables, field annotations, add newly added fields in the spider automatically, and fix common storage problems such
as field encoding, Data too long, and non-existent storage fields.

## Install

> `python 3.8.1+` can directly enter the following command:

```shell
pip install ayugespidertools -i https://pypi.org/simple
```

## Usage

> Developers only need to generate a sample template according to the command, and then configure the relevant settings.

Here's an example of how to use it in a GIF:

![ayugespidertools.gif](./examples/ayugespidertools-use.gif)

The steps in the above GIF are explained as follows:

```shell
# View library version
ayuge version

# Create project
ayuge startproject <project_name>

# Enter the project root directory
cd <project_name>

# Replace (or overwrite) with the actual configuration .conf file:
# This is just for demonstration purposes. Normally, you can simply fill in the required configuration in the .conf file under the VIT path.
# Unnecessary configuration can be set to empty, ignored, or deleted according to personal preference.
cp /root/mytemp/.conf DemoSpider/VIT/.conf

# Generate spider script
ayuge genspider <spider_name> <example.com>

# Run script
scrapy crawl <spider_name>
# Note: you can also use ayuge crawl <spider_name>
```

Please refer to the tutorial in the [DemoSpider](https://github.com/shengchenyang/DemoSpider) project or
the [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/) documentation for specific scenario examples. The
following scenarios are currently supported:

```diff
Scenario of storing data in Mysql:
+ 1).demo_one: Get mysql configuration based on .conf in local VIT.
+ 3).demo_three: Get the mysql configuration from consul.
+ 5).demo_five: Scenario of asynchronously storing data in MySQL.

Scenario of storing data in MongoDB:
+ 2).demo_two: Get mongodb configuration based on .conf in local VIT.
+ 4).demo_four: Get mongodb configuration from consul.
+ 6).demo_six: Scenario of asynchronously storing data in MongoDB.

- 7).demo_seven: Scenarios using requests to request (this feature has been removed, and using aiohttp is recommended instead)
+ 8).demo_eight: Scenario of storing data in both MySQL and MongoDB at the same time.
+ 9).demo_aiohttp_example: Scenarios using aiohttp to request.
+ 10).demo_aiohttp_test: Example of using scrapy aiohttp in a specific project.

+ 11).demo_proxy_one: Example of using dynamic tunnel proxy with "kuaidaili.com".
+ 12).demo_proxy_two: Example of using dedicated proxies with "kuaidaili.com".
+13).demo_AyuTurboMysqlPipeline: Example of using synchronous connection pooling with MySQL.
+14).demo_crawl: Example of supporting scrapy CrawlSpider.

# Example of supporting Item "Loaders feature" in this library(Documentation address：https://ayugespidertools.readthedocs.io/en/latest/topics/loaders.html)
+15).demo_item_loader: Example of using Item Loaders in this library.
-16).demo_item_loader_two: This example has been removed. You can refer to the example in the previous demo_item_loader. Currently, it is very convenient to use the Item Loaders feature.

+17).demo_mongo_async: Example of pipelines for storing data in MongoDB with asyncio version.
+18).demo_mq: Template example of storing data in RabbitMQ.
+19).demo_kafka: Template example of storing data in Kafka.
+20).demo_file: Template example of downloading images and other files to the local machine.
```

## Run Through The Test

Prerequisite: You need to create a `.conf` file in the `VIT` directory of the `tests`, and an example file has been
provided. Please fill in the required content for testing, then:

- You can directly use tox to run the tests.

- As this library is developed with [poetry](https://python-poetry.org/docs/), you can simply run `poetry install` in a
  new environment, and then manually run the target test or the pytest command for testing.

- Alternatively, you can use the make tool, run `make start`, and then `make test`.

## Things You Might Care About

1. If you find that the implementation of certain features in certain scenarios does not meet your expectations and you
   want to modify or add custom functionality, such as removing unused modules or modifying the library name, you can
   modify it yourself and then build it.

2. This library mainly promotes the functionality of the scrapy extension (i.e. the enhanced version of the custom
   template). In theory, using this library should not affect your scrapy project and other components.

3. If you want to contribute to this project, please refer to the [example](https://ayugespidertools.readthedocs.io/en/latest/additional/contribute.html) pull request.

## Build Your Own Library

> Please refer to the official documentation of [poetry](https://python-poetry.org/docs/) for specific content.

As mentioned in the section [Things You Might Care About](# Things You Might Care About), you can clone the source code
and modify any methods (e.g. you may need a different default log configuration value or add other project structure
templates for your project scenario), and then package and use it by running `poetry build` or `make build` after
modification.

For example, if you need to update pymongo in the dependency library to a new version `x.x.x`, you can simply install
the existing dependencies with `poetry install`, and then install the target version with `poetry add pymongo@x.x.x` (
try not to use `poetry update pymongo`). After ensuring that the test is working properly, you can package the modified
library with `poetry build` for use.

**I hope that this project can provide guidance for you when you encounter scenarios where you need to extend the
functionality of Scrapy.**

## Features

- [x] Scenarios for extending the functionality of Scrapy:
    - [x] Scrapy script runtime information statistics and project dependency table collection statistics can be used
      for logging and alerts.
    - [x] Custom templates that generate template files suitable for this library when
      using `ayuge startproject <projname>` and `ayuge genspider <spidername>`.
    - [x] ~~Add the functionality of obtaining configuration based on nacos.~~ -> Change to the functionality of
      obtaining configuration based on consul.
    - [x] Proxy middleware (dedicated proxy, dynamic tunnel proxy).
    - [x] Random User-Agent middleware.
    - [x] Use the following tools to replace scrapy's Request for sending requests:
        - [x] ~~`requests`: Using the synchronous library requests will reduce the efficiency of scrapy.~~（This feature
          has been removed, and using aiohttp is now recommended instead.）
        - [x] `aiohttp`: Integrated the coroutine method of replacing scrapy Request with aiohttp.
    - [x] Adaptation for scenarios where storage is done in Mysql:
        - [x] Automatically create the required databases, tables, field formats, and field comments for scenarios where
          Mysql users need to be created.
    - [x] Adaptation for scenarios where storage is done in MongoDB, with coding style consistent with storage in Mysql
      and other scenarios.
    - [x] Examples of asyncio syntax support and third-party library support for async:
        - [x] Example of using asyncio and aiohttp in a spider script.
        - [x] Example of using asyncio and aioMysql in a pipeline script.
    - [x] Integration of data push functions for Kafka, RabbitMQ, etc.
- [x] Common development scenarios:
    - [x] Concatenation of sql statements, only for simple scenarios, with further optimization to be done. Improvement
      directions and reference libraries have been provided.
    - [x] Concatenation of MongoDB statements.
    - [x] Formatting data processing, such as removing web page tags, removing unnecessary spaces, etc.
    - [x] Methods for restoring font-encrypted text to its original form to bypass anti-spider measures:
        - [x] Based on mapping of font files such as ttf and woff, or combined with css, etc.
            - [x] For font files where the mapping relationship can be found directly in the xml file, you can export
              the mapping using the [FontForge](https://github.com/fontforge/fontforge/releases) tool.
            - [x] For font files where the mapping relationship cannot be found, OCR recognition (with less than 100%
              accuracy) is generally used. First, each mapping is exported as a png using fontforge, and then various
              methods are used for recognition.
    - [x] Processing of HTML data, including removal of tags, invisible characters, and conversion of special characters
      to normal display, etc.
    - [x] Common methods for processing image CAPTCHA:
        - [x] Methods for recognizing the distance of the missing part of a slider captcha (with multiple implementation
          options).
        - [x] Methods for generating a trajectory array based on the distance of a slider.
        - [x] Identification of the position and click order of click-based CAPTCHAs, with suboptimal results that
          require further optimization.
        - [x] Example methods for restoring images that have been randomly disordered and mixed up.

Notice: I will include the function demo in the [readthedocs](https://ayugespidertools.readthedocs.io/en/latest/)
documentation to avoid overwhelming this section with too much content.
