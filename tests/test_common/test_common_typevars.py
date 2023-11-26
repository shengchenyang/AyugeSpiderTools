import threading

from ayugespidertools.common.typevars import DatabaseEngineClass


class TestDatabaseEngineClass:
    def setup_method(self):
        self.mysql_url1 = self._splice_engine_url(database="fir")
        self.mysql_url2 = self._splice_engine_url(database="sec")

    def _splice_engine_url(
        self,
        user: str = "root",
        password: str = "pwd",
        host: str = "localhost",
        port: int = 3306,
        database: str = "demo",
        charset: str = "utf8mb4",
    ):
        return (
            f"mysql+pymysql://{user}"
            f":{password}@{host}"
            f":{port}/{database}"
            f"?charset={charset}"
        )

    def test_normal(self):
        mysql_engine1 = DatabaseEngineClass(engine_url=self.mysql_url1)
        mysql_engine2 = DatabaseEngineClass(engine_url=self.mysql_url1)
        mysql_engine3 = DatabaseEngineClass(engine_url=self.mysql_url2)
        assert mysql_engine1 is mysql_engine2
        assert all(
            [mysql_engine1 is not mysql_engine3, mysql_engine2 is not mysql_engine3]
        )

    def test_multi_threaded(self):
        def create_engine_instance(engine_url):
            _instance = DatabaseEngineClass(engine_url)
            instances.append(_instance)

        instances = []
        threads = []
        for _ in range(10):
            thread = threading.Thread(
                target=create_engine_instance, args=(self.mysql_url1,)
            )
            threads.append(thread)
            thread.start()
            thread.join()
        assert all(instances[0] is instance for instance in instances[1:])

        instances.clear()
        threads.clear()
        for i in range(10):
            _mysql_url = self._splice_engine_url(database=str(i))
            thread = threading.Thread(target=create_engine_instance, args=(_mysql_url,))
            threads.append(thread)
            thread.start()
            thread.join()
        assert all(instances[0] is not instance for instance in instances[1:])
