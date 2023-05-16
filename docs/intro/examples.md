# 例子

本教程将引导您完成这些任务：

- 快速熟悉 `ayugespidertools` 库的使用方法和支持场景
- 编写爬虫来抓取站点并提取数据

## 1. 快速开始

> 你可以使用以下两种方式来快速开始

### 1.1. 方式一：ayugespidertools

> 通过跑通本库 `Github` 中的 `GIF` 示例

具体请点击跳转至 [AyugeSpiderTools](https://github.com/shengchenyang/AyugeSpiderTools) 查看

### 1.2. 方式二：DemoSpider

> 通过另一个的演示项目 `DemoSpider` 来选择复现某些场景

最好的学习方法是通过 `Github` 上的 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 示例，您可以使用它快速复现某些场景下的功能。

本库 `ayugespidertools` 的 [github README.md](https://github.com/shengchenyang/AyugeSpiderTools#readme) 中所有功能，都可以在 `DemoSpider` 中找到示例。

`DemoSpider` 项目位于：https://github.com/shengchenyang/DemoSpider ，您可以在项目的自述文件中找到有关它的更多信息。

## 2. 应用场景介绍

根据 `DemoSpider` 中的各个 `spider` 对一些应用场景进行简要的补充介绍，总体的介绍为：

```diff
# 采集数据存入 `Mysql` 的场景：
+ 1).demo_one: 配置根据本地 `settings` 的 `LOCAL_MYSQL_CONFIG` 中取值
+ 3).demo_three: 配置根据 `consul` 的应用管理中心中取值
+ 5).demo_five: 异步存入 `Mysql` 的场景

# 采集数据存入 `MongoDB` 的场景：
+ 2).demo_two: 采集数据存入 `MongoDB` 的场景（配置根据本地 `settings` 的 `LOCAL_MONGODB_CONFIG` 中取值）
+ 4).demo_four: 采集数据存入 `MongoDB` 的场景（配置根据 `consul` 的应用管理中心中取值）
+ 6).demo_six: 异步存入 `MongoDB` 的场景

# 将 `Scrapy` 的 `Request`，`FormRequest` 替换为其它工具实现的场景
- 以上为使用 scrapy Request 的场景
+ 7).demo_seven: scrapy Request 替换为 requests 请求的场景(一般情况下不推荐使用，同步库
+ 会拖慢 scrapy 速度，可用于测试场景)

+ 8).demo_eight: 同时存入 Mysql 和 MongoDB 的场景

+ 9).demo_aiohttp_example: scrapy Request 替换为 aiohttp 请求的场景，提供了各种请求场景示例（GET,POST）
+ 10).demo_aiohttp_test: scrapy aiohttp 在具体项目中的使用方法示例

+ 11).demo_proxy_one: 快代理动态隧道代理示例
+ 12).demo_proxy_two: 测试快代理独享代理

+13).demo_AyuTurboMysqlPipeline: mysql 同步连接池的示例
+14).demo_crawl: 支持 scrapy CrawlSpider 的示例

# 本库中给出支持 Item Loaders 特性的示例(文档地址：https://ayugespidertools.readthedocs.io/en/latest/topics/loaders.html)
+15).demo_item_loader: 本库中使用 Item Loaders 的示例
-16).demo_item_loader_two: 展示本库使用 itemLoader 特性的示例，此示例已删除，可查看上个 demo_item_loader 中的示例，目标已经可以很方便的使用 Item Loaders 功能了

+17).demo_mongo_async: asyncio 版本存储 mongoDB 的 pipelines 示例
```

基本查看查看以上 `spider` 即可了解使用方法，但有些示例还是不够详细，对以上内容进行补充。

- 以上场景有需要 `consul` 上的相关配置的示例，是根据 `.conf` 中的配置并按照小写风格书写，以下为 `json` 格式配置的示例：

  ```json
  {
      "mysql":{
          "host":"***",
          "port":3306,
          "user":"***",
          "password":"***",
          "database":"***",
          "charset":"utf8mb4"
      },
      "mongodb":{
          "host":"***",
          "port":27017,
          "user":"***",
          "password":"***",
          "database":"***",
          "authsource":"***"
      },
      "consul":{
          "token":"",
          "url":"http://host:port/v1/kv/...?dc=dc1",
          "format":"json"
      },
      "kdl_dynamic_proxy":{
          "proxy":"o668.kdltps.com:15818",
          "username":"***",
          "password":"***"
      },
      "kdl_exclusive_proxy":{
          "proxy":"http://kps.kdlapi.com/api/getkps?orderid=***&num=100&format=json",
          "username":"***",
          "password":"***",
          "index":1
      },
      "ali_oss":{
          "accesskeyid":"LTA***",
          "accesskeysecret":"***",
          "endpoint":"https://oss-cn-***.aliyuncs.com",
          "bucket":"***",
          "doc":"***"
      }
  }
  ```

  
