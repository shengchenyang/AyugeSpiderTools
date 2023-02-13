# Item Loaders

`Item Loaders` 提供了一种方便的机制来填充已抓取的 `ITEM`。尽管项目可以直接填充，项目加载器提供了一个更方便的 `API` 来从抓取过程中填充它们，通过自动化一些常见的任务，比如在分配它之前解析原始提取的数据。

换句话说，`ITEM` 提供了抓取数据的*容器，而项目加载器提供了**填充**该容器的机制。

`Item Loaders` 旨在提供一种灵活、高效和简单的机制来扩展和覆盖不同的字段解析规则，无论是通过蜘蛛，还是通过源格式（`HTML`、`XML` 等），而不会成为维护的噩梦。

## 使用方法

具体请查看 `scrapy` 中对应的 [Item Loaders](https://docs.scrapy.org/en/latest/topics/loaders.html) 的文档。

由文档可知，如果使用 `Item Loaders` 需要先声明 `Item` 子类，并固定 `Field` 字段。即以下内容：

```python
import scrapy

class Product(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    stock = scrapy.Field()
    tags = scrapy.Field()
    last_updated = scrapy.Field(serializer=str)
```

但是本库不推荐每次都自定义重写 `Item` 的 `Field` 字段，这样丧失了解放双手的目的。由上一章可知，本库只提供公共常用且固定的字段。

那本库如何实现使用项目加载器填充项目的效果呢，本库是通过 `ItemLoader` 配合 `make_dataclass` 的方法，不过这也丢失了优雅便捷性。

## 使用项目加载器填充项目

这是 `Spider` 中典型的 `Item Loader` 用法：

```python
from scrapy.loader import ItemLoader
from myproject.items import Product

def parse(self, response):
    l = ItemLoader(item=Product(), response=response)
    l.add_xpath('name', '//div[@class="product_name"]')
    l.add_xpath('name', '//div[@class="product_title"]')
    l.add_xpath('price', '//p[@id="price"]')
    l.add_css('stock', 'p#stock')
    l.add_value('last_updated', 'today') # you can also use literal values
    return l.load_item()
```

## 使用 dataclass items

本库中 `Item` 中的除了 `ScrapyClassicItem`，其它均为此类。

## 输入和输出处理器

那么，在本库中的使用方法如下：

`Item Loader` 包含一个输入处理器和一个用于每个 `item` 字段的输出处理器。输入处理器在收到数据后立即处理提取的数据（通过[`add_xpath()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_xpath),[`add_css()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_css)或 [`add_value()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_value)方法），输入处理器的结果被收集并保存在 `ItemLoader` 中。收集完所有数据后， [`ItemLoader.load_item()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.load_item)调用该方法填充并获取填充的 [项对象](https://docs.scrapy.org/en/latest/topics/items.html#topics-items)。那是使用先前收集的数据（并使用输入处理器处理）调用输出处理器的时候。输出处理器的结果是分配给项目的最终值。

让我们看一个示例来说明如何为特定字段调用输入和输出处理器（这同样适用于任何其他字段）：

### ScrapyClassicItem

本库是为了用手动管理 `item` 模块，比如需存储的字段数量，字段类型等；
其需要存储的字段全部放在 `alldata` 的 `item` 字段中，可以自定义扩展，但是无法使用 `Item Loaders` 的 `add_value` 等特性
若要支持 `Item Loaders` 的特性，需要自己补充完整 `item` 字段，比如下面代码：

```python
# 先补充需要管理的 item 字段
ScrapyClassicItem.fields["add_key1"] = scrapy.Field()
ScrapyClassicItem.fields["add_key2"] = scrapy.Field()
```

然后就可以使用 [使用项目加载器填充项目](# 使用项目加载器填充项目) 中的代码了

### make_dataclass

本库中的 `MysqlDataItem` 和 `MongoDataItem` 已经使用了 `@dataclass` 的装饰器了，
不再很优雅和方便地对其扩展字段了，推荐使用 `make_dataclass` 自行设置

```python
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
```

以上，可以发现 `scrapy` 也是推荐固定 `Item` 字段的，需要什么类型的字段就提前创建好其字段。

本库中 `Item` 则是直接将存储字段全存到 `alldata` 中即可。本库主推便捷，不太推荐使用以上代码自定义增加 `Item` 字段来适配 `Item Loaders` 的特性，除非某些场景下使用 `Item Loaders` 能够极大方便开发时，才推荐使用下。
