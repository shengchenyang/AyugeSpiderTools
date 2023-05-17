from itemadapter import ItemAdapter
from itemloaders.processors import TakeFirst
from scrapy.loader import ItemLoader

from ayugespidertools.items import DataItem, MongoDataItem, MysqlDataItem, ScrapyItem


def test_items_MysqlDataItem():
    mdi = MysqlDataItem(_table="table")
    mdi.add_field("field1", "value1")
    mdi.add_field("field2", "value2")
    mdi._table = "table1"
    mdi._item_mode = "Mysql"
    mdi["field3"] = DataItem(key_value="field3_key", notes="key值")
    assert all(
        [
            type(mdi) == MysqlDataItem,
            mdi._table == "table1",
            mdi._item_mode == "Mysql",
            mdi.fields == ["field1", "field2", "field3"],
        ]
    )

    mdi_dict = mdi.asdict()
    assert all(
        [
            type(mdi_dict) == dict,
            mdi_dict["field1"] == "value1",
            mdi_dict
            == {
                "field1": "value1",
                "field2": "value2",
                "field3": DataItem(key_value="field3_key", notes="key值"),
                "_table": "table1",
                "_item_mode": "Mysql",
            },
        ],
    )

    mdi_item = mdi.asitem()
    assert all(
        [
            type(mdi_item) == ScrapyItem,
            ItemAdapter.is_item(mdi_item),
            mdi_item["field1"] == "value1",
        ]
    )

    # 另一种赋值方式
    mdi_sec = MysqlDataItem(
        _table="table_one",
        field1="value1",
        field2="value2",
        field3=DataItem(key_value="field3_key", notes="key值"),
    )
    mdi_sec_dict = mdi_sec.asdict()
    assert all(
        [
            type(mdi_sec) == MysqlDataItem,
            mdi_sec_dict
            == {
                "_table": "table_one",
                "field1": "value1",
                "field2": "value2",
                "field3": DataItem(key_value="field3_key", notes="key值"),
                "_item_mode": "Mysql",
            },
        ]
    )

    # 以下是 item loaders 的使用
    test_item = MysqlDataItem(
        _table="table1",
        book_name=None,
    )
    mine_item = ItemLoader(item=test_item.asitem(), selector=None)
    mine_item.default_output_processor = TakeFirst()
    mine_item.add_value("_table", "_table_data_sec")
    mine_item.add_value("book_name", "book_name_data22")
    item = mine_item.load_item()
    assert all(
        [
            ItemAdapter.is_item(item),
            dict(item)
            == {
                "_item_mode": "Mysql",
                "_table": "table1",
                "book_name": "book_name_data22",
            },
        ]
    )


def test_items_MongoDataItem():
    mdi = MongoDataItem(
        _table="table_third",
        _mongo_update_rule={"title": "title_data"},
        field1="value1",
    )

    print("mmmm:", mdi)
    mdi_dict = mdi.asdict()
    assert all(
        [
            type(mdi_dict) == dict,
            mdi_dict
            == {
                "_table": "table_third",
                "_mongo_update_rule": {"title": "title_data"},
                "field1": "value1",
                "_item_mode": "MongoDB",
            },
        ]
    )

    mdi_item = mdi.asitem()
    assert all(
        [
            ItemAdapter.is_item(mdi_item),
            mdi_item["field1"] == "value1",
        ]
    )

    # 以下是 item loaders 的使用
    test_item = MongoDataItem(
        _table="table1",
        _mongo_update_rule={"title": "title_data"},
        book_name=None,
    )
    print("ttttt:", test_item)
    mine_item = ItemLoader(item=test_item.asitem(), selector=None)
    mine_item.default_output_processor = TakeFirst()
    # 注意，此处不会修改 _table 的值，如果想要修改，需要
    # 把 test_item 中的 _table 初始化为 None 即可重新赋值。比如 book_name 字段。
    mine_item.add_value("_table", "_table_data_sec")
    mine_item.add_value("book_name", "book_name_data22")
    item = mine_item.load_item()
    print("iiiii:", item, type(item), item["book_name"], dict(item))
    assert all(
        [
            ItemAdapter.is_item(item),
            dict(item)
            == {
                "_item_mode": "MongoDB",
                "_mongo_update_rule": {"title": "title_data"},
                "_table": "table1",
                "book_name": "book_name_data22",
            },
        ]
    )
