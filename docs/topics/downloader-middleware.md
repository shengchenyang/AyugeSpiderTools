# downloader-middleware

> 介绍本库中自带的常用 `DOWNLOADER_MIDDLEWARES` 中间件。

需要使用本库中的配置，需要在 `spider` 中修改如下，此为前提：

```python
from ayugespidertools.spiders import AyuSpider


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

## 3. 发送请求库改为 requests

### 3.1. 使用方法

激活 `DOWNLOADER_MIDDLEWARES` 中的对应配置。

```python
custom_settings = {
    "DOWNLOADER_MIDDLEWARES": {
        # 替换 scrapy Request 请求为 requests 的中间件
        "ayugespidertools.middlewares.RequestsDownloaderMiddleware": 401,
    },
}
```

然后在 `spdier` 中正常 `yield scrapy.Request` 即可。

## 4. 发送请求方式改为 aiohttp

### 4.1. 使用方法

激活 `DOWNLOADER_MIDDLEWARES` 中的对应配置。

```python
custom_settings = {
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "DOWNLOADER_MIDDLEWARES": {
        # 将 scrapy Request 替换为 aiohttp 方式
        "ayugespidertools.middlewares.AiohttpDownloaderMiddleware": 543,
    },
    # scrapy Request 替换为 aiohttp 的配置示例
    "LOCAL_AIOHTTP_CONFIG": {
        "timeout": 2,
        "proxy": "http://127.0.0.1:7890",
        "sleep": 1,
        "retry_times": 3,
    },
}
```

注：

- `TWISTED_REACTOR` 的配置在本库的 `settings` 中就默认打开的，这里配置是为了演示，不用再次配置的；
- `LOCAL_AIOHTTP_CONFIG` 为 aiohttp 的全局配置，一般可用来配置 `proxy`，`timeout`，`retry_times`， `sleep` 等全局的参数的；

然后需要构造 `AiohttpRequest` 或 `AiohttpFormRequest` 请求对象，具体的 `aiohttp` 参数在 `args` 中配置：

具体使用习惯和方式看个人选择，如下：

```python
# 方式一： 通过 args 参数传值
yield AiohttpRequest(
    url="http://httpbin.org/get?get_args=1",
    callback=self.parse_get_fir,
    meta={
        "meta_data": "这是用来测试 parse_get_fir meta 的功能",
    },
    args=AiohttpRequestArgs(
        method="GET",
        headers={
            "Cookie": "headers_ck_key1=ck; headers_ck_key2=ck",
        },
        cookies={
            "ck_key": "ck",
        },
    ),
    dont_filter=True,
)

# 方式二：使用 scrapy 传统方式传值
yield AiohttpRequest(
    url="http://httpbin.org/get?get_args=1",
    callback=self.parse_get_fir,
    headers={
        "Cookie": "headers_ck_key1=ck; headers_ck_key2=ck",
    },
    cookies={
        "ck_key": "ck",
    },
    meta={
        "meta_data": "这是用来测试 parse_get_fir meta 的功能",
    },
    dont_filter=True,
)

# 同样，发送 post 也可以选择两种方式
# 测试 POST 请求示例一 - normal
post_data = {"post_key1": "post_value1", "post_key2": "post_value2"}
yield AiohttpRequest(
    url="http://httpbin.org/post",
    method="POST",
    callback=self.parse_post_fir,
    headers={
        "Cookie": "headers_ck_key=ck; headers_ck_key2=ck",
    },
    body=json.dumps(post_data),
    cookies={
        "ck_key": "ck",
    },
    meta={
        "meta_data": "这是用来测试 parse_post_fir meta 的功能",
    },
    cb_kwargs={
        "request_name": "normal_post1",
    },
    dont_filter=True,
)
# 测试 POST 请求示例一 - aiohttp args
yield AiohttpRequest(
    url="http://httpbin.org/post",
    callback=self.parse_post_fir,
    args=AiohttpRequestArgs(
        method="POST",
        headers={
            "Cookie": "headers_ck_key=ck; headers_ck_key2=ck",
        },
        cookies={
            "ck_key": "ck",
        },
        data=json.dumps(post_data),
    ),
    meta={
        "meta_data": "这是用来测试 parse_post_fir meta 的功能",
    },
    cb_kwargs={
        "request_name": "aiohttp_post1",
    },
    dont_filter=True,
)

# 测试 POST 请求示例二 - normal
yield AiohttpFormRequest(
    url="http://httpbin.org/post",
    headers={
        "Cookie": "headers_ck_key=ck; headers_ck_key2=ck",
    },
    cookies={
        "ck_key": "ck",
    },
    formdata=post_data,
    callback=self.parse_post_sec,
    meta={
        "meta_data": "这是用来测试 parse_post_sec meta 的功能",
    },
    cb_kwargs={
        "request_name": "normal_post2",
    },
    dont_filter=True,
)
# 测试 POST 请求示例二 - aiohttp args
yield AiohttpFormRequest(
    url="http://httpbin.org/post",
    callback=self.parse_post_sec,
    args=AiohttpRequestArgs(
        method="POST",
        headers={
            "Cookie": "headers_ck_key=ck; headers_ck_key2=ck",
        },
        cookies={
            "ck_key": "ck",
        },
        data=post_data,
    ),
    meta={
        "meta_data": "这是用来测试 parse_post_sec meta 的功能",
    },
    cb_kwargs={
        "request_name": "aiohttp_post2",
    },
    dont_filter=True,
)
```

