# Configuration

`AyugeSpiderTools` 将项目中的所依赖的敏感信息放入了项目的 `VIT` 下的 `.conf` 文件中独立管理。

若你有多个过多的 `scrapy` 项目需要管理，你可以统一指定 `.conf` 所在文件夹的 `VIT_DIR` 路径参数。

若你还有过多的机器需要维护，更推荐使用本库中的 `consul` 及 `nacos` 扩展来远程配置管理，灵活性更高。

下面来介绍 `.conf` 文件中的配置内容：

## Introduction

配置格式使用 `ini`。

## [nacos]

[nacos](https://nacos.io) 可用于远程配置管理服务，可以更敏捷和容易地管理微服务平台。

| 参数名 | 参数备注                       | 描述                                                                                                    |
| ------ | ------------------------------ |-------------------------------------------------------------------------------------------------------|
| url    | _                              | nacos 服务对应的链接，若有鉴权参数请在 url 中构建。                                                                       |
| format | Literal["json", "xml", "yaml"] | nacos url 配置中对应的格式解析方法，支持 json，xml，yaml 解析。请优先使用 json 和 xml 来解析，yaml 解析需要安装 ayugespidertools[all] 依赖。 |

## [consul]

[consul](https://consul.io) 的配置管理功能同 `nacos`，是本库提供的另一选择。但请注意：`consul` 比 `nacos` 的优先级更高，如果两者都配置了会优先使用 `consul` 配置。

不同的是配置中的鉴权 `token` 参数独立了出来。

| 参数名 | 参数备注                              | 描述                                           |
| ------ | ------------------------------------- |----------------------------------------------|
| url    | _                                     | consul 服务对应的链接。                              |
| format | Literal["json", "xml", "yaml", "hcl"] | consul url 配置中对应的格式解析方法，支持 json，xml，yaml 解析。 |
| token  | 可选，默认空                          | consul token 参数。                             |

## [mysql]

用于 `mysql` 存储相关场景中使用，比如创建对应的 `sqlalchemy` 的 `engine`，`engine_conn` 来用于去重，创建数据库连接来解决表格缺失，字段缺失等问题。

| 参数名      | 参数备注                      | 描述                                                         |
| ----------- | ----------------------------- | ------------------------------------------------------------ |
| user        | _                             | _                                                            |
| password    | _                             | _                                                            |
| database    | _                             | 链接的数据库名称，在非 aiomysql 场景下，当 database 不存在时会用当前 user 创建所需库表及字段等。 |
| host        | 可选，默认 localhost          | _                                                            |
| port        | 可选，默认 3306               | _                                                            |
| engine      | 可选，默认 InnoDB             | 自动创建数据库和数据表时需要的参数                           |
| collate     | 可选，默认 utf8mb4_general_ci | 自动创建数据库和数据表时需要的参数                           |
| charset     | 可选，默认 utf8mb4            | 自动创建数据库和数据表时需要的参数                           |
| odku_enable | 可选，默认 false              | 是否开启 ON DUPLICATE KEY UPDATE 功能                        |

注：

- `charset` 参数选择有 `Literal["utf8mb4", "gbk", "latin1", "utf16", "utf16le", "cp1251", "euckr", "greek"]`，`charset` 要与 `collate` 参数匹配。
- 其中 `engine`，`charset`，`collate` 为自动创建数据库和数据表时需要的参数，可随意配置或默认即可，也可提前手动创建好表，也可后续手动修改。

## [mongodb:uri]

`mongodb` 链接的 `uri` 配置方式。

| 参数名 | 参数备注 | 描述        |
| ------ | -------- | ----------- |
| uri    | _        | mongoDB uri |

## [mongodb]

`mongodb` 链接的普通方式，`[mongodb:uri]` 和 `[mongodb]` 按需选择一种即可。 若两种都设置了，会优先从 `mongodb:uri` 中获取配置。

| 参数名        | 参数备注               | 描述 |
| ------------- | ---------------------- | ---- |
| database      | _                      | _    |
| user          | _                      | _    |
| password      | _                      | _    |
| host          | 可选，默认 localhost   | _    |
| port          | 可选，默认 27017       | _    |
| authsource    | 可选，默认 admin       | _    |
| authMechanism | 可选，默认 SCRAM-SHA-1 | _    |

## [postgresql]

用于 `postgresql` 存储相关场景中使用，比如创建对应的 `sqlalchemy` 的 `engine`，`engine_conn` 来用于去重，创建数据库连接来解决表格缺失，字段缺失等问题。

| 参数名   | 参数备注             | 描述                                                         |
| -------- | -------------------- | ------------------------------------------------------------ |
| user     | _                    | _                                                            |
| password | _                    | _                                                            |
| database | _                    | _                                                            |
| host     | 可选，默认 localhost | _                                                            |
| port     | 可选，默认 5432      | _                                                            |
| charset  | 可选，默认 UTF8      | 同 mysql 一样，用于在表不存在而创建时需要，可随意配置，后续也可手动修改。 |

## [elasticsearch]

用于 `elasticsearch` 存储相关场景中使用，也具有对应的 `es_engine`，`es_engine_conn` 来用于存储前的去重(查询及更新等自定义)逻辑。

| 参数名                 | 参数备注                                  | 描述                                                         |
| ---------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| hosts                  | _                                         | 若有多个，用逗号分隔，比如 https://x.x.x.x:9200,https://x.x.x.x:9201 |
| index_class            | 默认 {"settings":{"number_of_shards": 2}} | es Document 中的配置，比如 {"settings":{"number_of_shards": 2}} |
| user                   | 默认 elastic                              | _                                                            |
| password               | 默认 elastic                              | _                                                            |
| init                   | 是否初始化 es Document，默认 false        | 是否创建 es 索引，此设置一般只在第一次运行项目时打开，或者选择手动创建并配置此参数永远为 false。 |
| verify_certs           | 默认 false                                | 证书验证，推荐开启                                           |
| ca_certs               | 默认 None                                 | ca_certs 路径                                                |
| client_cert            | 默认 None                                 | client_cert 路径                                             |
| client_key             | 默认 None                                 | client_key 路径                                              |
| ssl_assert_fingerprint | 默认 None                                 | es 启动中的 HTTP CA certificate SHA-256 fingerprint 参数     |

注：`ca_certs`，`client_cert`，`client_key`，`ssl_assert_fingerprint` 中只用配置一个即可，若 `verify_certs` 设置为 `false` 则都不用配置以上参数，但推荐开启此参数。

## [mq]

推送到 `RabbitMQ`  场景所需的参数。以下配置参数与 `pika` 中一致，这里放入 [pika 文档](https://pika.readthedocs.io/en/stable/)，请自行对照查看。

| 参数名      | 参数备注             | 描述 |
| ----------- | -------------------- | ---- |
| virtualhost | _                    | _    |
| queue       | _                    | _    |
| exchange    | _                    | _    |
| routing_key | _                    | _    |
| username    | 可选，默认 guest     | _    |
| password    | 可选，默认 guest     | _    |
| host        | 可选，默认 localhost | _    |
| port        | 可选，默认 5672      | _    |

## [oracle]

用于 `oracle` 存储相关场景中使用，比如创建对应的 `sqlalchemy` 的 `engine`，`engine_conn` 来用于去重，但不会处理数据库表及字段缺失等错误，请提前创建好，因为其部分报错不如 `mysql` 及 `postgresql` 那样清晰明了，虽然也能解决，但必要性不高。

| 参数名        | 参数备注             | 描述                                        |
| ------------- | -------------------- | ------------------------------------------- |
| user          | _                    | _                                           |
| password      | _                    | _                                           |
| service_name  | _                    | _                                           |
| host          | 可选，默认 localhost | _                                           |
| port          | 可选，默认 1521      | _                                           |
| encoding      | 可选，默认 utf8      | oracledb 的链接参数。                       |
| thick_lib_dir | 可选，默认 false     | oracledb 的 thick_mode 所需参数，按需配置。 |

## [kafka]

推送到 `kafka` 场景所需的参数。以下配置参数与 `kafka-python` 中一致，这里放入 [kafka-python 文档](https://kafka-python.readthedocs.io/en/master/)，请自行对照查看。

| 参数名            | 参数备注 | 描述                                                 |
| ----------------- | -------- | ---------------------------------------------------- |
| bootstrap_servers | _        | 若有多个，用逗号分隔。比如 x.x.x.x:9092,x.x.x.x:9093 |
| topic             | _        | _                                                    |
| key               | _        | _                                                    |

## [kdl_dynamic_proxy]

快代理动态代理配置参数。

| 参数名   | 参数备注 | 描述                 |
| -------- | -------- | -------------------- |
| proxy    | _        | 快代理动态代理 api。 |
| username | _        | _                    |
| password | _        | _                    |

## [kdl_exclusive_proxy]

快代理动态代理配置参数。

| 参数名   | 参数备注     | 描述                       |
| -------- | ------------ | -------------------------- |
| proxy    | _            | 快代理独享代理 api。       |
| username | _            | _                          |
| password | _            | _                          |
| index    | 可选，默认 1 | 表示取其索引值对应的代理。 |

## [oss:ali]

上传到阿里云 oss 的配置参数。

| 参数名                   | 参数备注              | 描述                                                |
|-----------------------|-------------------|---------------------------------------------------|
| access_key            | _                 | 阿里云 access_key_id                                 |
| access_secret         | _                 | 阿里云账号对应的 access_key_secret                        |
| endpoint              | _                 | 填写 Bucket 所在地域对应的 Endpoint                        |
| bucket                | -                 | Bucket                                            |
| doc                   | -                 | 需要操作的文件夹目录，比如 file/img，为可选参数。                     |
| upload_fields_suffix  | 规则字段              | 上传到 oss 的字段规则，包含 upload_fields_suffix 后缀的字段会上传到 oss。 |
| oss_fields_prefix     | 规则字段              | 上传到 oss 的字段生成的新字段规则，会在原字段添加 oss_fields_prefix 前缀。 |
| full_link_enable      | 是否开启完整链接，默认 false | 为是否保存完整的 oss 文件链接，默认 false。                       |

遵守规则时的 `oss` 上传逻辑时使用，但更推荐自行实现和构建 `AyuItem` 的方式。具体请看 `demo_oss` 和 `demo_oss_sec` 的场景示例。请自行选择可接受的风格。
