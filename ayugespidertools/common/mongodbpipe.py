from abc import ABC, abstractmethod

from itemadapter import ItemAdapter

from ayugespidertools.common.multiplexing import ReuseOperation
from ayugespidertools.common.params import Param

__all__ = [
    "Synchronize",
    "TwistedAsynchronous",
    "AsyncioAsynchronous",
    "mongodb_pipe",
]


class AbstractClass(ABC):
    """
    用于处理 mongodb pipeline 存储的模板方法类
    """

    def _get_collection_name(self, table: str, collection_prefix: str = "") -> str:
        """
        获取集合名称
        Args:
            table: item 中的 table 字段
            collection_prefix: 集合前缀

        Returns:
            full_collection_name: 完整的集合名称
        """
        assert isinstance(table, str), "item 中 table 字段不是 str，或未传入 table 参数"
        full_collection_name = f"""{collection_prefix}{table}"""

        assert (
            " " not in full_collection_name
        ), "集合名不能含空格，请检查 MONGODB_COLLECTION_PREFIX 参数和 item 中的 table 参数"
        return full_collection_name

    def _get_insert_data(
        self,
        item_dict: ItemAdapter,
    ) -> dict:
        """
        获取要插入的数据，将 item 中的存储数据提取出来
        Args:
            item_dict: item ItemAdapter 格式数据，可像字典一样操作

        Returns:
            None
        """
        insert_data = item_dict.get("alldata")
        # 如果有 alldata 字段，则其为推荐格式
        if all([insert_data, isinstance(insert_data, dict)]):
            judge_item = next(iter(insert_data.values()))
            # 判断数据中中的 alldata 的格式：
            #     1.推荐：是嵌套 dict，就像 AyuMysqlPipeline 一样 -- 这是为了通用写法风格；
            #     2.是单层的 dict
            # 是 namedtuple 类型
            if ReuseOperation.is_namedtuple_instance(judge_item):
                insert_data = {v: insert_data[v].key_value for v in insert_data.keys()}
            # 如果是嵌套 dict 格式的话，需要再转化为正常格式
            elif isinstance(judge_item, dict):
                insert_data = {
                    v: insert_data[v]["key_value"] for v in insert_data.keys()
                }

        # 否则为旧格式
        else:
            insert_data = ReuseOperation.get_items_except_keys(
                dict_conf=item_dict,
                key_list=["table", "item_mode", "mongo_update_rule"],
            )
        return insert_data

    def process_item_template(
        self,
        item_dict: ItemAdapter,
        db: Param.PymongoDataBase,
        collection_prefix: str = "",
    ) -> None:
        """
        模板方法，用于处理 mongodb pipeline 存储的模板方法类
        Args:
            item_dict: item ItemAdapter 格式数据
            db: mongodb 数据库连接
            collection_prefix: 集合前缀

        Returns:
            None
        """
        insert_data = self._get_insert_data(item_dict)
        # 真实的集合名称为：集合前缀名 + 集合名称
        collection_name = self._get_collection_name(
            table=item_dict["table"],
            collection_prefix=collection_prefix,
        )
        self._data_storage_logic(
            db=db,
            item_dict=item_dict,
            collection_name=collection_name,
            insert_data=insert_data,
        )

    @abstractmethod
    def _data_storage_logic(
        self,
        db: Param.PymongoDataBase,
        item_dict: ItemAdapter,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        """
        数据存储逻辑，需要子类实现
        Args:
            db: mongodb 数据库连接
            item_dict: item ItemAdapter 格式数据
            collection_name: 集合名称
            insert_data: 要插入的数据
            *args: 可变参数
            **kwargs:关键字参数

        Returns:
            None
        """
        pass


class Synchronize(AbstractClass):
    """
    pipeline 同步执行 mongodb 存储的场景
    """

    def _data_storage_logic(
        self,
        db: Param.PymongoDataBase,
        item_dict: ItemAdapter,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        # 如果没有查重字段时，就直接插入数据（不去重）
        if not item_dict.get("mongo_update_rule"):
            db[collection_name].insert(insert_data)
        else:
            db[collection_name].update(
                item_dict["mongo_update_rule"], {"$set": insert_data}, True
            )


class TwistedAsynchronous(AbstractClass):
    """
    pipeline twisted 异步执行 mongodb 存储的场景
    """

    def _data_storage_logic(
        self,
        db: Param.PymongoDataBase,
        item_dict: ItemAdapter,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        if not item_dict.get("mongo_update_rule"):
            db[collection_name].insert(insert_data)
        else:
            db[collection_name].update(
                item_dict["mongo_update_rule"], {"$set": insert_data}, True
            )


class AsyncioAsynchronous(AbstractClass):
    """
    pipeline asyncio 异步执行 mongodb 存储的场景 - 使用 motor 实现
    """

    async def _data_storage_logic(
        self,
        db: Param.PymongoDataBase,
        item_dict: ItemAdapter,
        collection_name: str,
        insert_data: dict,
        *args,
        **kwargs,
    ) -> None:
        if not item_dict.get("mongo_update_rule"):
            await db[collection_name].insert_one(insert_data)
        else:
            await db[collection_name].update_many(
                item_dict["mongo_update_rule"], {"$set": insert_data}, True
            )

    async def process_item_template(
        self,
        item_dict: ItemAdapter,
        db: Param.PymongoDataBase,
        collection_prefix: str = "",
    ) -> None:
        insert_data = self._get_insert_data(item_dict)
        # 真实的集合名称为：集合前缀名 + 集合名称
        collection_name = self._get_collection_name(
            table=item_dict["table"],
            collection_prefix=collection_prefix,
        )
        await self._data_storage_logic(
            db=db,
            item_dict=item_dict,
            collection_name=collection_name,
            insert_data=insert_data,
        )


def mongodb_pipe(
    abstract_class: AbstractClass,
    item_dict: ItemAdapter,
    db: Param.PymongoDataBase,
    collection_prefix: str = "",
) -> None:
    """
    mongodb pipeline 存储的通用调用方法
    """
    abstract_class.process_item_template(
        item_dict=item_dict, db=db, collection_prefix=collection_prefix
    )
