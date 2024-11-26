from __future__ import annotations

from typing import TYPE_CHECKING

from gridfs import GridFS
from pymongo import MongoClient

from ayugespidertools.common.typevars import DatabaseSingletonMeta

__all__ = [
    "MongoDbBase",
    "MongoDBEngineClass",
]

if TYPE_CHECKING:
    from pymongo.database import Database

    from ayugespidertools.common.typevars import authMechanismStr


class MongoDBEngineClass(metaclass=DatabaseSingletonMeta):
    """mongodb 连接单例模式：同一个 engine_url 只能存在一个 conn 实例"""

    def __init__(self, engine_url, *args, **kwargs):
        self.engine = MongoDbBase.connects(uri=engine_url)


class MongoDbBase:
    """mongodb 数据库的相关操作"""

    @staticmethod
    def connects(
        user: str | None = None,
        password: str | None = None,
        host: str = "localhost",
        port: int = 27017,
        authsource: str = "admin",
        authMechanism: authMechanismStr = "SCRAM-SHA-1",
        database: str | None = None,
        uri: str | None = None,
    ) -> tuple[MongoClient, Database]:
        """初始化 mongo 连接句柄
        可传入 user, password, host 等参数的形式，也可只传入 uri 的方式

        Args:
            user: 用户名
            password: 用户对应的密码
            host: mongoDB 链接需要的 host
            port: mongoDB 链接需要的端口
            authsource: mongoDB 身份验证需要的数据库名称
            authMechanism: mongoDB 身份验证机制
            database: mongoDB 链接需要的数据库
            uri: mongoDB uri，需要包含 database 参数， demo: 'mongodb://host/my_database'
        """
        if uri is not None:
            conn: MongoClient = MongoClient(uri)
            db = conn.get_database()

        else:
            if database is None:
                raise ValueError(
                    "When URI is not provided, 'database' must be specified."
                )

            conn = MongoClient(
                host=host,
                port=port,
                username=user,
                password=password,
                authSource=authsource,
                authMechanism=authMechanism,
            )
            db = conn[database]
        return conn, db

    @staticmethod
    def getFileMd5(db, _id, collection):
        gridfs_col = GridFS(db, collection)
        gf = gridfs_col.get(_id)
        md5 = gf.md5
        _id = gf._id
        return {"_id": _id, "md5": md5}

    @classmethod
    def upload(cls, db, file_name, _id, content_type, collection, file_data):
        """上传文件

        Args:
            db: 目标库对应连接
            file_name: 上传至 mongoDB 的 GridFS 存储桶里的文件名
            _id: 唯一 id，雪花 id，用来标识此上传任务和图片的唯一
            content_type: 上传文件的类型，示例：image/jpeg
            collection: 存储至 GridFS 存储桶名称
            file_data: 文件的 bytes 内容

        Returns:
            gridfs_id: 上传至 GridFS 上的文件 ID 标识
            image_id: 上传至 GridFS 上的文件 MD5 标识
        """
        metadata = {
            "_contentType": content_type,
            "isThumb": "true",
            "targetId": _id,
            "_class": "com.ccr.dc.admin.mongo.MongoFsMetaData",
        }

        gridfs_col = GridFS(db, collection)
        # 当存储桶中不存在此文件，才需要上传
        if not gridfs_col.exists(filename=file_name):
            gridfs_id = gridfs_col.put(
                data=file_data,
                content_type=content_type,
                filename=file_name,
                metadata=metadata,
            )
            md5 = cls.getFileMd5(db, gridfs_id, "fs")["md5"]
            image_id = f"/file/find/{str(gridfs_id)}/{md5}"
            return gridfs_id, image_id

        # 否则，只需返回文件的 id 等标识即可
        res = gridfs_col.find_one({"filename": file_name})
        return res._id, f"/file/find/{str(res._id)}/{res.md5}"
