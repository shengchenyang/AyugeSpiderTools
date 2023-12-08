from typing import TYPE_CHECKING, Dict, List, Optional

from gridfs import GridFS
from pymongo import MongoClient

__all__ = [
    "MongoDbBase",
]

if TYPE_CHECKING:
    from ayugespidertools.common.typevars import authMechanismStr


class MongoDbBase:
    """mongodb 数据库的相关操作（此功能暂时为残废状态，请参考 pymilk 库中的实现）"""

    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: str = "localhost",
        port: int = 27017,
        authsource: str = "admin",
        authMechanism: "authMechanismStr" = "SCRAM-SHA-1",
        database: Optional[str] = None,
        uri: Optional[str] = None,
    ) -> None:
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
            self.conn = MongoClient(uri)
            self.db = self.conn.get_database()

        else:
            self.conn = MongoClient(
                host=host,
                port=port,
                username=user,
                password=password,
                authSource=authsource,
                authMechanism=authMechanism,
            )
            self.db = self.conn[database]

    def insert_one(self, collection: str, data: dict) -> str:
        """插入一条数据

        Args:
            collection: 集合名称
            data: 插入的数据

        Returns:
            inserted_id: 成功返回的 id
        """
        ret = self.db[collection].insert_one(data)
        return ret.inserted_id

    def insert_many(self, collection: str, data: List[Dict]):
        """批量插入

        Args:
            collection: 集合名称
            data: 插入的数据数组

        Returns:
            inserted_ids: list: 成功返回的 ids
        """
        ret = self.db[collection].insert_many(data)
        return ret.inserted_ids

    def update(self, collection, data):
        """更新

        Args:
            collection: 集合名称
            data: 更新的数据，{key:[old_data,new_data]}

        Returns:
            modified_count: 更新影响的个数
        """
        data_filter = {}
        data_revised = {}
        for key in data.keys():
            data_filter[key] = data[key][0]
            data_revised[key] = data[key][1]
        return (
            self.db[collection]
            .update_many(data_filter, {"$set": data_revised})
            .modified_count
        )

    def find(self, collection, condition, column: Optional[dict] = None):
        """查询

        Args:
            collection: 集合名称
            condition: 查询条件
            column:

        Returns:
            1). 查询条件的搜索结果
        """
        try:
            if column is None:
                return self.db[collection].find(condition)
            else:
                return self.db[collection].find(condition, column)
        except Exception as e:
            return f"查询数据格式有误{e}"

    def t_update(self, collection, s_key, s_value, update_data):
        # self.db.get_collection(collection).update_one({s_key: s_value}, {"$set": update_data})
        return (
            self.db[collection]
            .update_one({s_key: s_value}, {"$set": {"groupProps": update_data}})
            .modified_count
        )

    def update_normal(self, collection, s_key, s_value, data_style, update_data):
        return (
            self.db[collection]
            .update_one({s_key: s_value}, {"$set": {data_style: update_data}})
            .modified_count
        )

    def update_super(self, collection: str, select_dict: dict, set_dict: dict):
        """更新

        Args:
            collection: 需要更新的集合
            select_dict: 更新的条件
            set_dict: 更新的内容

        Returns:
            1). modified_count: int: 更新影响的数量
        """
        return (
            self.db[collection]
            .update_one(select_dict, {"$set": set_dict})
            .modified_count
        )

    # 删除
    def delete(self, collection, condition):
        return self.db[collection].delete_many(filter=condition).deleted_count

    # 上传数据
    def upload_file(self, file_name, collection, content_type, file_data, metadata):
        gridfs_col = GridFS(self.db, collection)
        return gridfs_col.put(
            data=file_data,
            content_type=content_type,
            filename=file_name,
            metadata=metadata,
        )

    def getFileMd5(self, _id, collection):
        gridfs_col = GridFS(self.db, collection)
        gf = gridfs_col.get(_id)
        md5 = gf.md5
        _id = gf._id
        return {"_id": _id, "md5": md5}

    def upload(self, file_name, _id, content_type, collection, file_data):
        """上传文件

        Args:
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

        gridfs_col = GridFS(self.db, collection)
        # 当存储桶中不存在此文件，才需要上传
        if not gridfs_col.exists(filename=file_name):
            gridfs_id = gridfs_col.put(
                data=file_data,
                content_type=content_type,
                filename=file_name,
                metadata=metadata,
            )
            md5 = self.getFileMd5(gridfs_id, "fs")["md5"]
            image_id = f"/file/find/{str(gridfs_id)}/{md5}"
            return gridfs_id, image_id

        # 否则，只需返回文件的 id 等标识即可
        res = gridfs_col.find_one({"filename": file_name})
        return res._id, f"/file/find/{str(res._id)}/{res.md5}"

    def __del__(self):
        if hasattr(self, "conn"):
            self.conn.close()
