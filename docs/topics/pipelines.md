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

#### 2.2.1。 twisted 实现

```python
# 依赖 AyuTwistedMongoPipeline
```

#### 2.2.2. asyncio motor 实现

```python
# 依赖 AsyncMongoPipeline
```
