# Configuration

`AyugeSpiderTools` 将项目中的所依赖的敏感信息放入了项目的 `VIT` 下的 `.conf` 文件中独立管理。

若你有多个过多的 `scrapy` 项目需要管理，你可以统一指定 `.conf` 所在文件夹的 `VIT_DIR` 路径参数。

若你还有过多的机器需要维护，更推荐使用本库中的 `consul` 及 `nacos` 扩展来远程配置管理，灵活性更高。

下面来介绍 `.conf` 文件中的配置内容：

## 整体介绍

其配置的格式使用 `ini`。

## nacos

TODO: 添加配置的详细说明！
