from dataclasses import field, make_dataclass

import scrapy
from itemadapter import ItemAdapter
from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader

from ayugespidertools.Items import MysqlDataItem, OldMongoDataItem, ScrapyClassicItem


def test_items():
    mdi = MysqlDataItem()
    mdi.table = "save_table_name"
    mdi.alldata = {"key1": "value1"}

    # 或者这样的数据格式
    # mdi.alldata = {"key1": {"key_value": "key_value_data1", "notes": "notes_data1"}}
    print("mdi:", mdi)
    print("mdi type:", type(mdi))

    d_adapter = ItemAdapter(mdi)
    all_data = d_adapter.get("alldata")
    print("get alldata data:", all_data)
    assert ItemAdapter.is_item(mdi)

    sci = ScrapyClassicItem()
    sci["table"] = "s_table"
    sci["alldata"] = {"s_all_data": 2}
    sci["item_mode"] = "Mysql"
    print("sci:", sci)
    print("sci type:", type(sci))

    a = {
        "alldata": {"k": "v"},
        "table": "save_table_name",
        "item_mode": "Mysql",
    }
    my_dict_adapter = ItemAdapter(a)
    all_data = my_dict_adapter.get("alldata")
    print("my alldata:", all_data, ItemAdapter.is_item(a))
    assert mdi is not None


def test_dataclass():
    # [1.] 本库中 ScrapyClassicItem 使用 add_value, add_xpath, add_css 的示例
    mine_item = ItemLoader(item=ScrapyClassicItem(), respnose=None)
    mine_item.default_output_processor = TakeFirst()
    mine_item.add_value("table", "save_table_name")
    item = mine_item.load_item()
    print("item:", item)

    """以下 [2.] [3.] 部分介绍扩展本库中 Item 字段以方便支持 add_value 等特性"""
    # [2.] ScrapyClassicItem 如何自定义增加字段，并支持 Item Loaders 的特性
    """
    本库是为了用手动管理 item 模块，比如需存储的字段数量，字段类型等；
    其需要存储的字段全部放在 alldata 的 item 字段中，可以自定义扩展，但是无法使用 Item Loaders 的 add_value 等特性
    若要支持 Item Loaders 的特性，需要自己补充完整 item 字段，比如下面代码：
    """
    # 先补充需要管理的 item 字段
    ScrapyClassicItem.fields["add_key1"] = scrapy.Field()
    ScrapyClassicItem.fields["add_key2"] = scrapy.Field()

    # 然后就可以使用 [1.] 中的代码了

    # [3.] 本库中 MysqlDataItem, MongoDataItem 如何自定义增加字段，并支持 Item Loaders 的特性
    """
    本库中的 MysqlDataItem 和 MongoDataItem 已经使用了 @dataclass 的装饰器了，
    不再很优雅和方便地对其扩展字段了，推荐使用 make_dataclass 自行设置
    """
    MineItem = make_dataclass(
        "MineItem",
        [
            ("book_name", str, field(default=None)),
            ("book_intro", str, field(default=None)),
            ("item_mode", str, field(default="Mysql")),
            ("table", str, field(default="save_table_name")),
        ],
    )

    mine_item = ItemLoader(item=MineItem(), selector=None)
    mine_item.default_output_processor = TakeFirst()
    mine_item.add_value("book_name", "book_name_data")
    # mine_item.add_xpath("book_intro", "get_book_intro_xpath")
    item = mine_item.load_item()
    print("item:", item)

    """
    以上，可以发现 scrapy 是推荐固定 Item 字段的，需要什么类型的字段就提前创建好其字段。
    本库中 Item 则是直接将存储字段全存到 alldata 中即可。
        本库主推便捷，不太推荐使用以上代码自定义增加 Item 字段来适配 Item Loaders 的特性，除非
        某些场景下使用 Item Loaders 能够极大方便开发时，才推荐使用下。
    """
