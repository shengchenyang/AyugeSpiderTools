from __future__ import annotations

from typing import TYPE_CHECKING

from gridfs import GridFS
from pymongo import MongoClient

from ayugespidertools.common.typevars import DatabaseSingletonMeta

__all__ = [
    "MongoDBEngineClass",
    "MongoDbBase",
]

if TYPE_CHECKING:
    from pymongo.database import Database

    from ayugespidertools.common.typevars import authMechanismStr


class MongoDBEngineClass(metaclass=DatabaseSingletonMeta):
    """Reuse a single MongoDB engine wrapper for each engine_url."""

    def __init__(self, engine_url, *args, **kwargs):
        self.engine = MongoDbBase.connects(uri=engine_url)


class MongoDbBase:
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
        """Create a MongoDB client and select a database.

        Supply either a URI or individual connection parameters.

        Args:
            user: Authentication username.
            password: Authentication password.
            host: MongoDB server hostname.
            port: MongoDB server port.
            authsource: Database used for authentication.
            authMechanism: MongoDB authentication mechanism.
            database: Database to select when no URI is supplied.
            uri: MongoDB URI containing a default database, for example:
                "mongodb://host/my_database". Overrides individual parameters.

        Returns:
            The MongoClient instance and selected database.
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
    def upload(
        cls, db, file_name, _id, content_type, collection, file_data
    ) -> tuple[int | None, str | None]:
        """Upload a file to GridFS unless a file with the same name already exists.

        Args:
            db: Destination MongoDB database.
            file_name: Filename stored in the GridFS bucket.
            _id: Identifier recorded as targetId in the file metadata.
            content_type: File MIME type, such as "image/jpeg".
            collection: GridFS bucket name.
            file_data: File contents as bytes.

        Returns:
            The GridFS file ID and a download path containing the ID and MD5 value,
            or (None, None) if an existing file cannot be retrieved.
        """
        metadata = {
            "_contentType": content_type,
            "isThumb": "true",
            "targetId": _id,
            "_class": "com.ccr.dc.admin.mongo.MongoFsMetaData",
        }

        gridfs_col = GridFS(db, collection)
        # Upload only if the bucket does not contain this filename.
        if not gridfs_col.exists(filename=file_name):
            gridfs_id = gridfs_col.put(
                data=file_data,
                content_type=content_type,
                filename=file_name,
                metadata=metadata,
            )
            md5 = cls.getFileMd5(db, gridfs_id, "fs")["md5"]
            image_id = f"/file/find/{gridfs_id!s}/{md5}"
            return gridfs_id, image_id

        # Reuse the existing file ID and download path.
        if res := gridfs_col.find_one({"filename": file_name}):
            return res._id, f"/file/find/{res._id!s}/{res.md5}"
        return None, None
