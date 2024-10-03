# Settings

`AyugeSpiderTools` 设置允许您自定义所有 `Scrapy` 及 `AyugeSpiderTools` 组件的行为，包括核心、扩展、管道和蜘蛛本身。

若您还不清楚 `Scrapy` 设置的知识，请跳转至 [Scrapy 文档](https://docs.scrapy.org/en/latest)查看教程。

以下内容主要介绍本库在具体场景下的配置示例：

## VIT_DIR

Default: `<project_dir>/<project_name>/VIT`

项目运行配置 `.conf` 的路径，用于存放项目在不同场景下的配置，比如数据库链接配置。

## logger

Default: `loguru.logger`

用于日志记录，可按需设置。可与 `scrapy` 中的 `LOG_LEVEL` 和 `LOG_FILE`一同设置。

```
logger.add(
    "logs/error.log",
    level="ERROR",
    rotation="1 week",
    retention="7 days",
    enqueue=True,
)
```

## LOGURU_ENABLED

Default: `True`

是否开启 `loguru` 日志记录功能，开启时 `slog.<Log levels>("This is a log.")`。
具体的说明请在 [logging](logging.md) 中查看。

## DATABASE_ENGINE_ENABLED

旧配置名：`MYSQL_ENGINE_ENABLED`，已删除此配置名称

Default: `False`

是否打开 `database` 引擎开关，用于数据入库前更新逻辑判断。
如果是 `mysql` 场景，打开此项会激活 `mysql_engine` 和 `mysql_engine_conn`;
如果是 `postgresql` 场景，打开此项会激活 `postgres_engine` 和 `postgres_engine_conn`;

## APP_CONF_MANAGE

Default: `False`

开启远程配置服务，支持 `consul` 和 `nacos` 工具，配合 `VIT_DIR` 中的 `.conf` 中的对应 `consul` 或 `nacos` 链接配置使用。
如果两者都有，那优先取值 `consul`，即优先级 `consul` 大于 `nacos`。

## AIOHTTP_CONFIG

Default:
```
{
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

这是使用 `aiohttp` 的 `yield AiohttpRequest` 来代替 `scrapy` 的 `yield Request` 和 `yield FormRequest` 来发送请求的功能；
其中的全局配置默配置全为 `None`，代表如果不配置其值或配置为 `None` 会使用 `aiohttp request` 的默认值，默认值示例如下：

```shell
# 除了 sleep 和 retry_times，其它配置的字段及其默认值和 aiohttp 的 aiohttp.TCPConnector 保持一致。
verify_ssl: bool = True,
fingerprint: Optional[bytes] = None,
use_dns_cache: bool = True,
ttl_dns_cache: Optional[int] = 10,
family: int = 0,
ssl_context: Optional[SSLContext] = None,
ssl: Union[bool, Fingerprint, SSLContext] = True,
local_addr: Optional[Tuple[str, int]] = None,
resolver: Optional[AbstractResolver] = None,
keepalive_timeout: Union[None, float, object] = sentinel,
force_close: bool = False,
limit: int = 100,
limit_per_host: int = 0,
enable_cleanup_closed: bool = False,
loop: Optional[asyncio.AbstractEventLoop] = None,
timeout_ceil_threshold: float = 5,
```

使用 `aiohttp` 来发送请求时，这个 `AIOHTTP_CONFIG` 及其子项不是必须参数，按需设置即可。现可使用统一的 `yield AiohttpRequest` 方式，且与 `aiohttp` 一样的请求参数来更方便地开发。

具体实例请查看 [downloader-middleware](downloader-middleware.md#3-发送请求方式改为-aiohttp) 的部分文档。
