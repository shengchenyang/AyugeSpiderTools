# How-To-Build-Your-Own-Library

本库由 `poetry` 包管理工具构建，任何修改本库后自定义打包等需求请以 [poetry](https://python-poetry.org/) 官方文档为准。

## 前言

本库是把 `Scrapy` 的一些常用功能（扩展功能和开发中常用方法）封装成了一个库，方便大家快速使用。

但在使用本库的过程中，你可能会遇到一些问题：

- 比如模板中某些配置不符合你的项目需求；
- 不喜欢项目结构的设计；
- 依赖库的版本不适合你的需求。

像这些可能包含非常个性化的定制，无法适配所有人的喜好，也无法通过 `Pull Requests` 合并来优雅地解决此类问题，这时候你可能会想要修改一些东西，那么你可以参考本文档，来快速构建你自己的专属库。

## 构建方法

你可以 `clone` 源码后，修改任意方法，修改完成后 `poetry build` 或 `make build` 即可打包并内部使用。

> 以更新 `kafka-python` 版本为例：

- Prepare: `clone` 项目并准备开发环境

  将项目克隆到本地，创建 `python` 虚拟环境并安装 `poetry`，然后在项目根目录下运行 `poetry install` 安装依赖即可。

- Make your changes: 自定义更改的内容

  修改你所关注的部分，比如你的项目场景下可能需要其它的日志配置默认值，或添加其它的项目结构模板，更改库名等。

  若需要更新本项目的 `kafka-python` 依赖库版本为 `x.x.x`，那只需 `poetry add kafka-python==x.x.x` 安装目标版本即可。

- Run tests & Rebuild: 测试功能并重打包

  修改完毕并测试可用后，即可通过 `poetry build` 或 `make` 工具的 `make build` 打包即可使用。

以上步骤可以简化为，先 `clone` 源码，然后做出改变（若构建 `preview` 包时则不需要变动），最后在虚拟环境中执行 `pip install poetry && poetry build` 即可打包。

## 补充

若你自定义的方法对大多数人都合适的话，可以尝试将此功能添加到本项目，但是在此之前请先提交相关的 `ISSUES` 确认可行后再开发和提交对应 `PULL REQUESTS`，以免浪费了你做出的贡献。
