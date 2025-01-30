from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.exceptions import NotConfigured

try:
    from elasticsearch_dsl import Document, connections
except ImportError:
    raise NotConfigured(
        "missing elasticsearch_dsl library, please install it. "
        "install command: pip install ayugespidertools[database]"
    )

__all__ = ["AyuESPipeline", "dynamic_es_document"]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import ESConf
    from ayugespidertools.spiders import AyuSpider

    DocumentType = Union[type[Document], type]


def dynamic_es_document(class_name, fields, index_settings=None):
    class_attrs = fields.copy()
    if index_settings:
        class_attrs["Index"] = type("Index", (), index_settings)

    return type(class_name, (Document,), class_attrs)


class AyuESPipeline:
    es_conf: ESConf
    es_type: DocumentType

    def open_spider(self, spider: AyuSpider) -> None:
        assert hasattr(spider, "es_conf"), "未配置 elasticsearch 连接信息！"
        self.es_conf = spider.es_conf
        _hosts_lst = self.es_conf.hosts.split(",")
        if any([self.es_conf.user is not None, self.es_conf.password is not None]):
            http_auth = (self.es_conf.user, self.es_conf.password)
        else:
            http_auth = None
        connections.create_connection(
            hosts=_hosts_lst,
            http_auth=http_auth,
            verify_certs=self.es_conf.verify_certs,
            ca_certs=self.es_conf.ca_certs,
            client_cert=self.es_conf.client_cert,
            client_key=self.es_conf.client_key,
            ssl_assert_fingerprint=self.es_conf.ssl_assert_fingerprint,
        )

    def process_item(self, item: Any, spider: AyuSpider) -> Any:
        item_dict = ReuseOperation.item_to_dict(item)
        alert_item = ReuseOperation.reshape_item(item_dict)
        if not (new_item := alert_item.new_item):
            return

        if not hasattr(self, "es_type"):
            fields_define = {k: v.notes for k, v in item_dict.items()}
            index_define = self.es_conf.index_class
            index_define["name"] = alert_item.table.name
            self.es_type = dynamic_es_document("ESType", fields_define, index_define)
            if self.es_conf.init:
                self.es_type.init()
        es_item = self.es_type(**new_item)
        es_item.save()
        return item
