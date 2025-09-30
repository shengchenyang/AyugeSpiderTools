from pymongo.uri_parser import parse_uri

from ayugespidertools.common.typevars import MongoDBConf
from ayugespidertools.utils.database import MongoDBAsyncPortal, MongoDBPortal
from tests import MONGODB_CONFIG


class TestUtilsDatabase:
    def setup_method(self):
        self.mongodb_uri = MONGODB_CONFIG["uri"]
        parsed = parse_uri(self.mongodb_uri)
        self.db_name = parsed["database"]
        self.mongodb_conf = MongoDBConf(uri=self.mongodb_uri)

    def test_mongodb_portal(self):
        mp = MongoDBPortal(db_conf=self.mongodb_conf)
        db_name = mp.connect().name
        mp_client = mp.get_client()
        db_name2 = mp_client.get_database().name
        assert db_name == db_name2 == self.db_name

    def test_mongodb_async_portal(self):
        map = MongoDBAsyncPortal(db_conf=self.mongodb_conf)
        db_name = map.connect().name
        map_client = map.get_client()
        db_name2 = map_client.get_database().name
        assert db_name == db_name2 == self.db_name
        map.close()
