from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from ayugespidertools.common.params import Param

if TYPE_CHECKING:
    import configparser
    from collections.abc import Callable


class ConfigHandler(ABC):
    section: ClassVar[str]
    target: ClassVar[str]

    @classmethod
    @abstractmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement the 'parse' method")


class ConfigRegistry:
    _handlers: ClassVar[dict[str, type[ConfigHandler]]] = {}
    _priority: ClassVar[dict[str, list[str]]] = {}
    _priority_sections: ClassVar[set[str]] = set()

    @classmethod
    def register(
        cls, section: str, target: str, priority: list[str] | None = None
    ) -> Callable[[type[ConfigHandler]], type[ConfigHandler]]:
        def decorator(handler_cls: type[ConfigHandler]) -> type[ConfigHandler]:
            if section in cls._handlers:
                raise ValueError(f"Handler for section '{section}' already registered")

            handler_cls.section = section
            handler_cls.target = target
            cls._handlers[section] = handler_cls
            if priority:
                cls._priority[target] = priority
                cls._priority_sections.update(priority)
            return handler_cls

        return decorator

    @classmethod
    def _iter_priority_handlers(cls, cfg):
        for target, sections in cls._priority.items():
            for section in sections:
                handler = cls._handlers.get(section)
                if handler and section in cfg:
                    yield target, handler
                    break

    @classmethod
    def parse_all(cls, cfg: configparser.ConfigParser, inner_settings: dict) -> dict:
        for target, handler in cls._iter_priority_handlers(cfg):
            inner_settings[target] = handler.parse(cfg)

        for section, handler in cls._handlers.items():
            if section in cls._priority_sections:
                continue
            if section in cfg:
                inner_settings[handler.target] = handler.parse(cfg)
        return inner_settings


@ConfigRegistry.register(section="mysql", target="MYSQL_CONFIG")
class MysqlHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        mysql_section = cfg[cls.section]
        _charset = mysql_section.get("charset", "utf8mb4")
        return {
            "host": mysql_section.get("host", "localhost"),
            "port": mysql_section.getint("port", 3306),
            "user": mysql_section.get("user", ""),
            "password": mysql_section.get("password", ""),
            "charset": _charset,
            "database": mysql_section.get("database", ""),
            "engine": mysql_section.get("engine", "InnoDB"),
            "collate": mysql_section.get(
                "collate",
                Param.charset_collate_map.get(_charset, "utf8mb4_general_ci"),
            ),
            "odku_enable": mysql_section.getboolean("odku_enable", False),
            "insert_ignore": mysql_section.getboolean("insert_ignore", False),
        }


@ConfigRegistry.register(
    section="mongodb:uri",
    target="MONGODB_CONFIG",
    priority=["mongodb:uri", "mongodb"],
)
class MongodbUriHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        return {"uri": cfg.get(cls.section, "uri", fallback=None)}


@ConfigRegistry.register(section="mongodb", target="MONGODB_CONFIG")
class MongodbHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        mongodb_section = cfg[cls.section]
        return {
            "host": mongodb_section.get("host", "localhost"),
            "port": mongodb_section.getint("port", 27017),
            "authsource": mongodb_section.get("authsource", "admin"),
            "authMechanism": mongodb_section.get("authMechanism", "SCRAM-SHA-1"),
            "user": mongodb_section.get("user", "admin"),
            "password": mongodb_section.get("password", None),
            "database": mongodb_section.get("database", None),
        }


@ConfigRegistry.register(section="postgresql", target="POSTGRESQL_CONFIG")
class PostgresqlHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        postgres_section = cfg[cls.section]
        return {
            "host": postgres_section.get("host", "localhost"),
            "port": postgres_section.getint("port", 5432),
            "user": postgres_section.get("user", "postgres"),
            "password": postgres_section.get("password", ""),
            "database": postgres_section.get("database", ""),
            "charset": postgres_section.get("charset", "UTF8"),
        }


@ConfigRegistry.register(section="elasticsearch", target="ES_CONFIG")
class ElasticSearchHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        es_section = cfg[cls.section]
        return {
            "hosts": es_section.get("hosts", None),
            "index_class": json.loads(
                es_section.get("index_class", '{"settings":{"number_of_shards": 2}}')
            ),
            "user": es_section.get("user", None),
            "password": es_section.get("password", None),
            "init": es_section.getboolean("init", False),
            "verify_certs": es_section.getboolean("verify_certs", False),
            "ca_certs": es_section.get("ca_certs", None),
            "client_cert": es_section.get("client_cert", None),
            "client_key": es_section.get("client_key", None),
            "ssl_assert_fingerprint": es_section.get("ssl_assert_fingerprint", None),
        }


@ConfigRegistry.register(section="oracle", target="ORACLE_CONFIG")
class OracleHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        oracle_section = cfg[cls.section]
        return {
            "host": oracle_section.get("host", "localhost"),
            "port": oracle_section.getint("port", 1521),
            "user": oracle_section.get("user", None),
            "password": oracle_section.get("password", None),
            "service_name": oracle_section.get("service_name", None),
            "thick_lib_dir": oracle_section.get("thick_lib_dir", False),
            "authentication_mode": oracle_section.get("authentication_mode", "DEFAULT"),
        }


@ConfigRegistry.register(
    section="consul", target="REMOTE_CONFIG", priority=["consul", "nacos"]
)
class ConsulHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        consul_section = cfg[cls.section]
        return {
            "token": consul_section.get("token", None),
            "url": consul_section.get("url", None),
            "format": consul_section.get("format", "json"),
            "remote_type": "consul",
        }


@ConfigRegistry.register(section="nacos", target="REMOTE_CONFIG")
class NacosHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        nacos_section = cfg[cls.section]
        return {
            "token": nacos_section.get("token", None),
            "url": nacos_section.get("url", None),
            "format": nacos_section.get("format", "json"),
            "remote_type": "nacos",
        }


@ConfigRegistry.register(section="proxy", target="PROXY_CONFIG")
class ProxyHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        proxy_section = cfg[cls.section]
        return {"proxy": proxy_section.get("proxy", None)}


@ConfigRegistry.register(section="mq", target="MQ_CONFIG")
class MQHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        mq_section = cfg[cls.section]
        _queue = mq_section.get("queue", None)
        return {
            "host": mq_section.get("host", "localhost"),
            "port": mq_section.getint("port", 5672),
            "username": mq_section.get("username", "guest"),
            "password": mq_section.get("password", "guest"),
            "virtualhost": mq_section.get("virtualhost", "/"),
            "heartbeat": mq_section.getint("heartbeat", 0),
            "socket_timeout": mq_section.getint("socket_timeout", 1),
            "queue": _queue,
            "durable": mq_section.getboolean("durable", True),
            "exclusive": mq_section.getboolean("exclusive", False),
            "auto_delete": mq_section.getboolean("auto_delete", False),
            "exchange": mq_section.get("exchange", ""),
            "routing_key": mq_section.get("routing_key", _queue),
            "content_type": mq_section.getint("content_type", "text/plain"),
            "delivery_mode": mq_section.getint("delivery_mode", 1),
            "mandatory": mq_section.getboolean("mandatory", True),
        }


@ConfigRegistry.register(section="kafka", target="KAFKA_CONFIG")
class KafkaHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        kafka_section = cfg[cls.section]
        return {
            "bootstrap_servers": kafka_section.get(
                "bootstrap_servers", "127.0.0.1:9092"
            ),
            "topic": kafka_section.get("topic", None),
            "key": kafka_section.get("key", None),
            "security_protocol": kafka_section.get("security_protocol", None),
            "sasl_mechanism": kafka_section.get("sasl_mechanism", None),
            "user": kafka_section.get("user", None),
            "password": kafka_section.get("password", None),
        }


@ConfigRegistry.register(section="oss:ali", target="OSS_CONFIG")
class OssHandler(ConfigHandler):
    @classmethod
    def parse(cls, cfg: configparser.ConfigParser) -> dict[str, Any]:
        oss_section = cfg[cls.section]
        return {
            "access_key": oss_section.get("access_key", None),
            "access_secret": oss_section.get("access_secret", None),
            "endpoint": oss_section.get("endpoint", None),
            "bucket": oss_section.get("bucket", None),
            "doc": oss_section.get("doc", None),
            "upload_fields_suffix": oss_section.get(
                "upload_fields_suffix", "_file_url"
            ),
            "oss_fields_prefix": oss_section.get("oss_fields_prefix", "_"),
            "full_link_enable": oss_section.getboolean("full_link_enable", False),
        }
