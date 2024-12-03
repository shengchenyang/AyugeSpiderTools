# downloader-middleware

> 介绍本库中自带的常用 `DOWNLOADER_MIDDLEWARES` 中间件。

需要使用本库中的配置，需要在 `spider` 中修改如下，此为前提：

```python
from ayugespidertools.spiders import AyuSpider


# 当前 spider 要继承 AyuSpider
class DemoOneSpider(AyuSpider): ...
```

## 1. 随机UA

> 使用 `fake_useragent` 库中的 `ua` 信息，在每次发送请求时将随机取 `ua` 信息，将比较常用的 `ua` 标识的权重设置高一点，这里是根据 `fake_useragent` 库中的打印信息来规划权重的，即类型最多的 `ua` 其权重也就越高。

### 1.1. 使用方法

只需激活 `DOWNLOADER_MIDDLEWARES` 对应的配置即可。

```python
custom_settings = {
    "DOWNLOADER_MIDDLEWARES": {
        # 随机请求头
        "ayugespidertools.middlewares.RandomRequestUaMiddleware": 400,
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
        "ayugespidertools.middlewares.DynamicProxyDownloaderMiddleware": 125,
    },
}
```

需要修改此项目中的 `VIT` 文件夹下的 `.conf` 对应的配置信息。

```ini
[KDL_DYNAMIC_PROXY]
PROXY=o668.kdltps.com:15818
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
        "ayugespidertools.middlewares.ExclusiveProxyDownloaderMiddleware": 125,
    },
}
```

需要修改此项目中的 `VIT` 文件夹下的 `.conf` 对应的配置信息。

```ini
[kdl_exclusive_proxy]
proxy=http://kps.kdlapi.com/api/getkps?orderid=***&num=100&format=json
username=***
password=***
index=1
```

注：`index` 为在有多个独享代理时取的代理对应的索引值。

## 3. 发送请求方式改为 aiohttp

### 3.1. 使用方法

激活 `DOWNLOADER_MIDDLEWARES` 中的对应配置。

```python
custom_settings = {
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "DOWNLOADER_MIDDLEWARES": {
        # 将 scrapy Request 替换为 aiohttp 方式
        "ayugespidertools.middlewares.AiohttpDownloaderMiddleware": 543,
    },
    # aiohttp.TCPConnector 的配置项，非必需项，按需配置
    "AIOHTTP_CONFIG": {
        "sleep": 1,
        # 同时连接的总数
        "limit": 100,
        # 同时连接到一台主机的数量
        "limit_per_host": 0,
        "retry_times": 3,
        "verify_ssl": False,
        "allow_redirects": False,
    },
    # aiohttp 的超时时间也用这个配置
    "DOWNLOAD_TIMEOUT": 25,
}
```

注：

- `TWISTED_REACTOR` 的配置在本库的 `settings` 中就默认打开的，这里配置是为了演示，不用再次配置的；
- 这里的 `scrapy DOWNLOAD_TIMEOUT` 同样也是 `aiohttp` 请求的超时设置参数；
- `AIOHTTP_CONFIG` 为 `aiohttp` 的全局配置，是构建 `aiohttp.ClientSession` 的 `connector` 时所需的参数；

`AIOHTTP_CONFIG` 可配置的参数如下(其实就是 `aiohttp.TCPConnector` 中的参数):

```python
AIOHTTP_CONFIG = {
    # 设置 aiohttp.TCPConnector 中的配置
    "verify_ssl": None,
    "fingerprint": None,
    "use_dns_cache": None,
    "ttl_dns_cache": None,
    "family": None,
    "ssl_context": None,
    "ssl": None,
    "local_addr": None,
    "resolver": None,
    "keepalive_timeout": None,
    "force_close": None,
    "limit": None,
    "limit_per_host": None,
    "enable_cleanup_closed": None,
    "loop": None,
    "timeout_ceil_threshold": None,
    # 设置一些自定义的全局参数
    "sleep": None,
    "retry_times": None,
}
```

目前版本简化了 `aiohttp` 在 `yield AiohttpRequest` 的操作，也删除了 `AiohttpFormRequest` 来简化流程，示例如下：

```python
from ayugespidertools.request import AiohttpRequest
from scrapy.http.request import NO_CALLBACK

_ar_headers_ck = "headers_ck_key=ck; headers_ck_key2=ck"
_ar_ck = {"ck_key": "ck"}


def request_example():
    # 发送 get 请求示例：
    yield AiohttpRequest(
        url="http://httpbin.org/get?get_args=1",
        callback=NO_CALLBACK,
        headers={"Cookie": _ar_headers_ck},
        cookies=_ar_ck,
        cb_kwargs={"request_name": 1},
    )

    # 发送 post 请求示例：
    post_data = {"post_key1": "post_value1", "post_key2": "post_value2"}
    yield AiohttpRequest(
        url="http://httpbin.org/post",
        method="POST",
        callback=NO_CALLBACK,
        headers={"Cookie": _ar_headers_ck},
        data=post_data,
        cookies=_ar_ck,
        cb_kwargs={"request_name": 2},
        dont_filter=True,
    )


# 其中 AiohttpRequest 中的 params，json，data，proxy，ssl，timeout 等参数可按需求自定义设置。
```
由于改成通过 `yield AiohttpRequest` 的统一接口发送请求，且此方法参数与 `aiohttp` 的请求参数一致，极大地减少用户使用成本和避免维护地狱。
