import pytest

from ayugespidertools.common.mongodbpipe import SyncStorageHandler, store_process
from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.items import AyuItem, DataItem
from tests.conftest import generate_random_code, mongodb_database, test_table


class TestMongoDBPipe:
    def setup_method(self):
        _article_title = f"_article_title_{generate_random_code()}"
        self._article_info = {
            "article_detail_url": DataItem("_article_detail_url", "文章详情链接"),
            "article_title": DataItem(_article_title, "文章标题"),
            "comment_count": DataItem("_comment_count", "文章评论数量"),
            "favor_count": DataItem("_favor_count", "文章赞成数量"),
            "nick_name": DataItem("_nick_name", "文章作者昵称"),
        }
        self._article_info_with_no_dataItem = {
            "article_detail_url": "_article_detail_url",
            "article_title": _article_title,
            "comment_count": "_comment_count",
            "favor_count": "_favor_count",
            "nick_name": "_nick_name",
        }

    @pytest.mark.usefixtures("mongodb_conn")
    def test_MongoDBPipe_with_AyuItem(self, mongodb_conn):
        item_normal = AyuItem(
            **self._article_info,
            _table=DataItem(test_table, "文章信息表"),
        )
        store_process(
            item_dict=ReuseOperation.item_to_dict(item_normal),
            db=mongodb_conn[mongodb_database],
            handler=SyncStorageHandler,
        )
        num = mongodb_conn[mongodb_database][test_table].count_documents(
            {"article_detail_url": "_article_detail_url"}
        )
        assert num >= 1

        self._article_info.update({"comment_count": DataItem(2, "文章评论数量")})
        item_with_update_rule = AyuItem(
            **self._article_info,
            _table=DataItem(test_table, "文章信息表"),
            _update_rule={
                "article_title": self._article_info["article_title"].key_value
            },
            _update_keys={"comment_count"},
        )
        store_process(
            item_dict=ReuseOperation.item_to_dict(item_with_update_rule),
            db=mongodb_conn[mongodb_database],
            handler=SyncStorageHandler,
        )
        num = mongodb_conn[mongodb_database][test_table].count_documents(
            {"article_detail_url": "_article_detail_url", "comment_count": 2}
        )
        assert num >= 1

    @pytest.mark.usefixtures("mongodb_conn")
    def test_mongodb_pipe_with_dict(self, mongodb_conn):
        item_dict = {
            **self._article_info_with_no_dataItem,
            "_table": test_table,
            "_update_rule": {
                "article_detail_url": "_article_detail_url",
            },
        }
        store_process(
            item_dict=ReuseOperation.item_to_dict(item_dict),
            db=mongodb_conn[mongodb_database],
            handler=SyncStorageHandler,
        )
        num = mongodb_conn[mongodb_database][test_table].count_documents(
            {"article_detail_url": "_article_detail_url"}
        )
        assert num >= 1

        item_dict = {
            "_table": test_table,
            "_update_rule": {
                "article_detail_url": "这条的查重规则应该会新增一条数据_",
            },
        }
        item_dict.update(
            {
                "article_detail_url": "_article_detail_url",
                "article_title": "_article_title",
                "comment_count": "_comment_count",
                "favor_count": "_favor_count",
                "nick_name": "_nick_name",
            }
        )
        item_dict = ReuseOperation.item_to_dict(item_dict)
        store_process(
            item_dict=item_dict,
            db=mongodb_conn[mongodb_database],
            handler=SyncStorageHandler,
        )
        num = mongodb_conn[mongodb_database][test_table].count_documents(
            {"article_detail_url": "_article_detail_url"}
        )
        assert num >= 2
