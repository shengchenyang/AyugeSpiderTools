# Settings

`AyugeSpiderTools` 设置允许您自定义所有 `Scrapy` 及 `AyugeSpiderTools` 组件的行为，包括核心、扩展、管道和蜘蛛本身。

若您还不清楚 `Scrapy` 设置的知识，请跳转至 https://docs.scrapy.org/en/latest 查看教程。

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
    "proxy": None,
    "sleep": None,
    "limit": None,
    "ssl": None,
    "verify_ssl": None,
    "limit_per_host": None,
    "allow_redirects": None,
    "retry_times": None,
    "verify_ssl": None,
    "allow_redirects": None,
}
```

其中的 `proxy`，`sleep` `proxy` `allow_redirects` `cookies` 会在 `meta` 中的 `args` 参数中重置，即这些参数在全局的优先级小于 `meta` 的 `args` 。
`timeout` 默认和 `scrapy` 的 `DOWNLOAD_TIMEOUT` 一致，如果想设置小于 `DOWNLOAD_TIMEOUT`，则在 `meta` 的 `args` 中设置。
其中的默认值请以`aiohttp`为准，这里统一为 `None`。
非常建议在 `DemoSpider` 项目中查看具体场景的示例代码。
