# Define conf for github action
# 这里先使用直接赋值的方式，暂时不使用 github secrets 的方式
# 不用担心以下设置会泄漏密码等隐私设置
mysql_conf = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "RootAyuge",
    "database": "demo",
    "engine": "InnoDB",
    "charset": "utf8mb4",
    "collate": "utf8mb4_general_ci",
}
mongodb_conf = {
    "host": "127.0.0.1",
    "port": 27017,
    "database": "demo",
    "authsource": "admin",
    "user": "admin",
    "password": "RootAyuge",
}
mongodb_uri_conf = {
    "uri": "mongodb://admin:RootAyuge@127.0.0.1:27017/demo?authSource=admin&authMechanism=SCRAM-SHA-1"
}
