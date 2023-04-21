# Release notes

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
