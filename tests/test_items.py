import pytest
from itemadapter import ItemAdapter
from itemloaders.processors import TakeFirst
from scrapy.loader import ItemLoader

from ayugespidertools.exceptions import EmptyKeyError, FieldAlreadyExistsError
from ayugespidertools.items import AyuItem, DataItem, ScrapyItem

cur_item = AyuItem(
    title="t",
    _table="table",
)


def test_items_AyuItem():
    mdi = AyuItem(_table="turbo")
    mdi.add_field("field1", "value1")
    # 目前 add_field 不允许重复添加和设置相同字段
    with pytest.raises(FieldAlreadyExistsError):
        mdi.add_field("_table", "table1")

    # 取值不存在 field 场景
    with pytest.raises(KeyError):
        _ = mdi["field12"]

    assert all(
        [
            mdi["_table"] == "turbo",
            mdi["field1"] == "value1",
        ],
    )

    # 修改 / 添加字段场景
    mdi["_table"] = "table"
    mdi["name"] = "ayuge"
    mdi["field2"] = DataItem(key_value="field2_key", notes="key值")
    assert all(
        [
            mdi["_table"] == "table",
            mdi["name"] == "ayuge",
            isinstance(mdi["field2"], DataItem),
            mdi["field2"].key_value == "field2_key",
            mdi["field2"].notes == "key值",
            mdi.fields() == {"_table", "field1", "field2", "name", "_conflict_cols"},
        ]
    )

    # 转字典场景
    mdi_dict = mdi.asdict()
    assert mdi_dict == {
        "field1": "value1",
        "field2": DataItem(key_value="field2_key", notes="key值"),
        "_table": "table",
        "name": "ayuge",
        "_conflict_cols": {"id"},
    }

    # 删除字段场景
    del mdi["name"]
    with pytest.raises(KeyError):
        _ = mdi["name"]
    # 删除字段规则修改: 删除不存在的字段时不再报错
    del mdi["no_this_field"]

    with pytest.raises(AttributeError):
        del mdi.no_this_field
    assert mdi.fields() == {"_table", "field1", "field2", "_conflict_cols"}

    # 转 ScrapyItem 场景
    mdi_item = mdi.asitem()
    assert all(
        [
            isinstance(mdi_item, ScrapyItem),
            ItemAdapter.is_item(mdi_item),
            mdi_item["_conflict_cols"] == {"id"},
        ]
    )

    mdi_item_sec = mdi.asitem(assignment=True)
    assert mdi_item_sec == {
        "_conflict_cols": {"id"},
        "_table": "table",
        "field1": "value1",
        "field2": DataItem(key_value="field2_key", notes="key值"),
    }

    # 另一种赋值方式
    mdi_sec = AyuItem(
        _table="table",
        field1="value1",
        field2=DataItem(key_value="field2_key", notes="key值"),
    )
    mdi_sec_dict = mdi_sec.asdict()
    assert mdi_sec_dict == {
        "_table": "table",
        "field1": "value1",
        "field2": DataItem(key_value="field2_key", notes="key值"),
        "_conflict_cols": {"id"},
    }

    # 以下是 item loaders 的使用
    test_item = AyuItem(
        _table="table",
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
                "_table": "table",
                "book_name": "book_name_data22",
                "_conflict_cols": {"id"},
            },
        ]
    )

    # 以下是包含去重更新的内置参数的情况
    mdi = AyuItem(
        title="t",
        field1="value1",
        _table="table",
        _update_rule={"title": "title_data"},
        _update_keys={"field1"},
    )

    mdi_dict = mdi.asdict()
    assert all(
        [
            isinstance(mdi_dict, dict),
            mdi_dict
            == {
                "_table": "table",
                "_update_rule": {"title": "title_data"},
                "_update_keys": {"field1"},
                "title": "t",
                "field1": "value1",
                "_conflict_cols": {"id"},
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
    test_item = AyuItem(
        _table="table",
        _update_rule={"title": "title_data"},
        book_name=None,
    )
    mine_item = ItemLoader(item=test_item.asitem(), selector=None)
    mine_item.default_output_processor = TakeFirst()
    # 注意，此处不会修改 _table 的值，如果想要修改，需要
    # 把 test_item 中的 _table 初始化为 None 即可重新赋值。比如 book_name 字段。
    mine_item.add_value("_table", "_table_data_sec")
    mine_item.add_value("book_name", "book_name_data22")
    item = mine_item.load_item()
    assert all(
        [
            ItemAdapter.is_item(item),
            dict(item)
            == {
                "_update_rule": {"title": "title_data"},
                "_table": "table",
                "book_name": "book_name_data22",
                "_conflict_cols": {"id"},
            },
        ]
    )


def test_empty_key_error():
    with pytest.raises(EmptyKeyError):
        cur_item.add_field(None, "title")

    with pytest.raises(EmptyKeyError):
        cur_item.add_field("", "title")


def test_field_already_exists_error():
    with pytest.raises(FieldAlreadyExistsError):
        cur_item.add_field("title", "title")


def test_getattr_field_in_fields():
    with pytest.raises(AttributeError):
        _ = cur_item.name


def test_iter_over_fields():
    item = AyuItem(_table="users", title="hello")
    item["age"] = 18
    item["name"] = "zhangsan"

    # 使用 __iter__ 得到字段列表
    fields = set(iter(item))
    assert fields == {
        "name",
        "title",
        "_conflict_cols",
        "age",
        "_table",
    }


def test_get_fields():
    user_data = AyuItem(_table="users", title="hello")
    with pytest.raises(AttributeError):
        _ = user_data.title


def test_len_fields():
    item = AyuItem(_table="users", title="hello")
    assert len(item) == 3


def test_copy_and_deepcopy():
    item = AyuItem(
        _table="users",
        title="hello",
        _update_rule={"title": "hello"},
        _update_keys={"title"},
    )

    copied = item.copy()
    deep_copied = item.deepcopy()

    assert all(
        [
            isinstance(copied, AyuItem),
            copied is not item,
            copied.asdict() == item.asdict(),
            copied["_update_rule"] is item["_update_rule"],
            copied["_update_keys"] is item["_update_keys"],
            isinstance(deep_copied, AyuItem),
            deep_copied is not item,
            deep_copied.asdict() == item.asdict(),
            deep_copied["_update_rule"] is not item["_update_rule"],
            deep_copied["_update_keys"] is not item["_update_keys"],
        ]
    )

    del item["_conflict_cols"]
    assert "_conflict_cols" not in item.copy()


def test_ayuge_and_scrapy_item():
    from scrapy import Field, Item

    class BookItem(Item):
        name = Field()
        profile = Field()

    # 测试 item 的默认浅拷贝
    profile = {"score": 89}
    book_item = BookItem(name="name_value", profile=profile)
    assert book_item["profile"] is profile
    profile["score"] = 96
    assert book_item["profile"]["score"] == 96

    # 测试 item 的浅拷贝
    copied = book_item.copy()
    assert copied is not book_item
    assert copied["profile"] is book_item["profile"]
    copied["profile"]["score"] = 20
    assert book_item["profile"]["score"] == 20

    # 测试 item 的深拷贝
    deep_copied = book_item.deepcopy()
    assert deep_copied["profile"] is not book_item["profile"]
    deep_copied["profile"]["score"] = 30
    assert book_item["profile"]["score"] == 20

    # 测试 AyuItem 的默认浅拷贝
    ayu_profile = {"score": 89}
    ayu_book_item = AyuItem(name="name_value", profile=ayu_profile)

    assert ayu_book_item["profile"] is ayu_profile
    ayu_profile["score"] = 96
    assert ayu_book_item["profile"]["score"] == 96

    # 测试 AyuItem 的浅拷贝
    ayu_copied = ayu_book_item.copy()
    assert ayu_copied is not ayu_book_item
    assert ayu_copied["profile"] is ayu_book_item["profile"]
    ayu_copied["profile"]["score"] = 20
    assert ayu_book_item["profile"]["score"] == 20

    # 测试 AyuItem 的深拷贝
    ayu_deep_copied = ayu_book_item.deepcopy()
    assert ayu_deep_copied["profile"] is not ayu_book_item["profile"]
    ayu_deep_copied["profile"]["score"] = 30
    assert ayu_book_item["profile"]["score"] == 20
