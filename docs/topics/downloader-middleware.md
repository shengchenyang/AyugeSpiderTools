# downloader-middleware

> 介绍本库中自带的常用 `DOWNLOADER_MIDDLEWARES` 中间件。

需要使用本库中的配置，需要在 `spider` 中修改如下，此为前提：

```python
from ayugespidertools.AyugeSpider import AyuSpider


# 当前 spider 要继承 AyuSpider
class DemoOneSpider(AyuSpider):
    ...
```

## 1. 随机UA

> 使用 `fake_useragent` 库中的 `ua` 信息，在每次发送请求时将随机取 `ua` 信息，将比较常用的 `ua` 标识的权重设置高一点，这里是根据 `fake_useragent` 库中的打印信息来规划权重的，即类型最多的 `ua` 其权重也就越高。

### 1.1. 使用方法

只需激活 `DOWNLOADER_MIDDLEWARES` 对应的配置即可。

```python
custom_settings = {
    "DOWNLOADER_MIDDLEWARES": {
        # 随机请求头
        "ayugespidertools.Middlewares.RandomRequestUaMiddleware": 400,
    },
}
```

若想查看是否正常运行，只需查看其 `scrapy` 的 `debug` 日志，或在 `spider` 中打印 `response` 信息然后查看其信息即可。

## 2. 代理

### 2.1. 动态隧道代理

> 本库以快代理为例，其各个代理种类的使用方法大致相同

#### 2.1.1. 使用方法

激活 `DOWNLOADER_MIDDLEWARES` 中的动态代理配置。

```python
custom_settings = {
    "DOWNLOADER_MIDDLEWARES": {
        # 动态隧道代理激活
        "ayugespidertools.Middlewares.DynamicProxyDownloaderMiddleware": 125,
    },
}
```

需要修改此项目中的 `VIT` 文件夹下的 `.conf` 对应的配置信息。

```ini
[KDL_DYNAMIC_PROXY]
PROXY_URL=o668.kdltps.com:15818
USERNAME=***
PASSWORD=***
```

然后即可正常运行。

### 2.2. 独享代理

#### 2.2.1. 使用方法

激活 `DOWNLOADER_MIDDLEWARES` 中的独享代理配置。

```python
custom_settings = {
    "DOWNLOADER_MIDDLEWARES": {
        # 独享代理激活
        "ayugespidertools.Middlewares.ExclusiveProxyDownloaderMiddleware": 125,
    },
}
```

需要修改此项目中的 `VIT` 文件夹下的 `.conf` 对应的配置信息。

```ini
[KDL_EXCLUSIVE_PROXY]
PROXY_URL=http://kps.kdlapi.com/api/getkps?orderid=***&num=100&format=json
USERNAME=***
PASSWORD=***
PROXY_INDEX=1
```

注：`PROXY_INDEX` 为在有多个独享代理时取的代理对应的索引值。

## 3. 发送请求库改为 requests

### 3.1. 使用方法

激活 `DOWNLOADER_MIDDLEWARES` 中的对应配置。

```python
custom_settings = {
    "DOWNLOADER_MIDDLEWARES": {
        # 替换 scrapy Request 请求为 requests 的中间件
        "ayugespidertools.Middlewares.RequestByRequestsMiddleware": 401,
    },
}
```

然后在 `spdier` 中正常 `yield scrapy.Request` 即可。
