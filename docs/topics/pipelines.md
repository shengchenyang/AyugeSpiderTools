# pipelines

> 介绍本库中自带的常用 `pipelines` 管道。

需要使用本库中的配置，需要在 `spider` 中修改如下，此为前提：

```python
from ayugespidertools.spiders import AyuSpider


# 当前 spider 要继承 AyuSpider
class DemoOneSpider(AyuSpider):
    ...
```

## 1. Mysql 存储

### 1.1. 普通存储

> `AyuFtyMysqlPipeline` 为 `mysql` 存储的普通模式，具有自动创建所需数据库，数据表，自动动态管理 table 字段，表注释，也会自动处理常见（字段编码，`Data too long`，存储字段不存在等等）的存储问题。

#### 1.1.1 使用方法

只需激活 `DOWNLOADER_MIDDLEWARES` 对应的配置即可。

```python
custom_settings = {
    "ITEM_PIPELINES": {
        # 激活此项则数据会存储至 Mysql
        "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 300,
    },
}
```

然后在 `spider` 中按照约定的格式进行 `yield item` 即可，具体请查看 [yield item](https://ayugespidertools.readthedocs.io/en/latest/topics/items.html#yield-item)，然后不用再去管 `pipelines` 了。

### 1.2. 异步存储

#### 1.2.1. twisted 实现

使用 `twisted` 的 `adbapi` 实现 `Mysql` 存储场景下的异步操作

##### 1.2.1.1. 使用方法

同样地，只需激活 `DOWNLOADER_MIDDLEWARES` 对应的配置即可。

```python
custom_settings = {
    "ITEM_PIPELINES": {
        # 激活此项则数据会存储至 Mysql
        "ayugespidertools.pipelines.AyuTwistedMysqlPipeline": 300,
    },
}
```

### 1.3. 运行日志记录

> 打开 `RECORD_LOG_TO_MYSQL` 参数会记录 `spider` 的运行情况和所依赖的数据库下（带有 `crawl_time` 字段的）所有表格的当前采集情况统计。

## 2. MongoDB 存储

> 这里就直接介绍其依赖方法，因为其它配置与上方 `Mysql` 场景一模一样

### 2.1. 普通存储

```python
# 依赖 AyuFtyMongoPipeline
```

### 2.2. 异步存储

#### 2.2.1. twisted 实现

```python
# 依赖 AyuTwistedMongoPipeline
```

#### 2.2.2. asyncio motor 实现

```python
# 依赖 AsyncMongoPipeline
```

## 3. 消息推送服务

### 3.1. mq

> 此场景下给出的是以 `pika` 实现的 `RabbitMQ` 的示例

需要激活 `ITEM_PIPELINES` 对应的配置，然后在 `.conf` 中配置 `mq` 相关配置。

`spider` 中的 `custom_settings` 所需配置如下：

```python
"ITEM_PIPELINES": {
    "ayugespidertools.pipelines.AyuMQPipeline": 300,
},
```

`.conf` 中的所需配置如下：

```ini
[mq]
host=***
port=5672
username=***
password=***
virtualhost=***
queue=***
exchange=***
routing_key=***

# 一般只需配置以上参数即可，因为会有一些默认值，如果不需更改则不用配置，比如以下为非必须参数及其默认值：
durable=True
exclusive=False
auto_delete=False
content_type="text/plain"
delivery_mode=1
mandatory=True
```

然后在 `spider` 中 `yield` 你所需结构的 `item` 即可（类型为 `dict`）。

### 3.2. kafka

> 此场景给出的是以 `kafka-python` 实现的 `kafka` 推送示例

需要激活 `ITEM_PIPELINES` 对应的配置，然后在 `.conf` 中配置 `mq` 相关配置。

`spider` 中的 `custom_settings` 所需配置如下：

```python
"ITEM_PIPELINES": {
    "ayugespidertools.pipelines.AyuKafkaPipeline": 300,
},
```

`.conf` 中的所需配置如下：

```ini
[kafka]
bootstrap_servers=127.0.0.1:9092 #若多个用逗号分隔
topic=***
key=***
```

然后在 `spider` 中 `yield` 你所需结构的 `item` 即可（类型为 `dict`）。

## 4. 文件下载

需要激活 `ITEM_PIPELINES` 对应的配置，然后在项目中配置相关参数。

`spider` 中的 `custom_settings` 所需配置如下：

```python
"ITEM_PIPELINES": {
    "ayugespidertools.pipelines.FilesDownloadPipeline": 300,
    # 以下 AyuFtyMysqlPipeline 非必须，但只激活 FilesDownloadPipeline 时只会下载文件，但是
    # 并不会将信息与网页中的标题、描述等信息绑定，激活 AyuFtyMysqlPipeline 之类的选项后，可以自行
    # 添加其它可以描述文件的详细字段并存储对应场景的数据库中。
    "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 301,
},
```

`spider` 等其它项目配置中的所需详细设置示例如下：

```ini
from DemoSpider.settings import DOC_DIR

...

custom_settings = {
    "ITEM_PIPELINES": {
        "ayugespidertools.pipelines.FilesDownloadPipeline": 300,
        "ayugespidertools.pipelines.AyuFtyMysqlPipeline": 301,
    },
    # 下载文件保存路径，不配置则默认为项目设置中的 DOC_DIR（需要确认此文件夹是否存在）
    "FILES_STORE": DOC_DIR,
}
```

具体示例请在 [DemoSpider](https://github.com/shengchenyang/DemoSpider) 项目中的 `demo_file` 查看。
