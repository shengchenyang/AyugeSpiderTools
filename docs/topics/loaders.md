# Item Loaders

`Item Loaders` 提供了一种方便的机制来填充已抓取的 `ITEM`。尽管项目可以直接填充，项目加载器提供了一个更方便的 `API` 来从抓取过程中填充它们，通过自动化一些常见的任务，比如在分配它之前解析原始提取的数据。

换句话说，`ITEM` 提供了抓取数据的容器，而项目加载器提供了**填充**该容器的机制。

`Item Loaders` 旨在提供一种灵活、高效和简单的机制来扩展和覆盖不同的字段解析规则，无论是通过蜘蛛，还是通过源格式（`HTML`、`XML` 等），而不会成为维护的噩梦。

具体请查看 `scrapy` 中对应的 [Item Loaders](https://docs.scrapy.org/en/latest/topics/loaders.html) 的文档。

由文档可知，如果使用 `Item Loaders` 需要先声明 `Item` 子类，并固定 `Field` 字段。即以下内容示例：

```python
import scrapy

class Product(scrapy.Item):
    book_name = scrapy.Field()
    book_href = scrapy.Field()
    book_intro = scrapy.Field()
```

但是本库不固定 `Item field` 的内容，这样丧失了解放双手的目的。

虽然，`scrapy` 也可以通过使用如下方法来新增字段，但总归 scrapy 是不推荐这样的写法且不太方便：

```python
Product.fields["add_field1"] = scrapy.Field()
```

那本库如何实现使用项目加载器填充项目的效果呢，本库是通过 `Item` 的 `asitem` 方法实现。具体使用方法请看文章后半段。

## 使用项目加载器填充项目

这是 `Spider` 中典型的 `Item Loader` 用法：

```python
from scrapy.loader import ItemLoader
from myproject.items import Product
from ayugespidertools.items import MongoDataItem, MysqlDataItem


# 这是 scrapy 中的实现示例：
def parse(self, response):
    l = ItemLoader(item=Product(), response=response)
    l.add_xpath('name', '//div[@class="product_name"]')
    l.add_xpath('name', '//div[@class="product_title"]')
    l.add_xpath('price', '//p[@id="price"]')
    l.add_css('stock', 'p#stock')
    l.add_value('last_updated', 'today') # you can also use literal values
    yield l.load_item()

# 这是本库中的实现示例：
def parse(self, response):
    # 先定义所需字段
    my_product = MysqlDataItem(
        book_name=None,
        book_href=None,
        book_intro=None,
        _table=TableEnum.article_list_table.value["value"],
    )
    # 然后可使用 asitem 的方法使用常规的 ItemLoader 功能
    mine_item = ItemLoader(item=my_product.asitem(), selector=None)
    mine_item.default_output_processor = TakeFirst()
    mine_item.add_value("book_name", book_name)
    mine_item.add_xpath("book_href", '//div[@class="product_title"]')
    mine_item.add_css("book_intro", 'p#stock')
    item = mine_item.load_item()
    yield item
```

## 使用数据类项

那本库的方式在使用 `ItemLoader` 时有没有缺点呢？

是的，有缺点，由于本库虽然支持动态添加 `Item` 字段，但是其实不太好实现 `dataclass items` 的字段类型约束和参数 `default` 的相关设置。本库是不推荐固定 `Item` 字段（比如 `ayugespidertools` `v3.0.0` 之前的版本中，会把数据都存入 `alldata` 的固定字段中），也不推荐不同 `spider` 就需要定义其对应的不同 `Item class` 的。其实各有优缺点，只是本库选择了牺牲此部分。

## 输入和输出处理器

那么，在本库中的使用方法如下：

`Item Loader` 包含一个输入处理器和一个用于每个 `item` 字段的输出处理器。输入处理器在收到数据后立即处理提取的数据（通过[`add_xpath()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_xpath),[`add_css()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_css)或 [`add_value()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.add_value)方法），输入处理器的结果被收集并保存在 `ItemLoader` 中。收集完所有数据后， [`ItemLoader.load_item()`](https://docs.scrapy.org/en/latest/topics/loaders.html#scrapy.loader.ItemLoader.load_item)调用该方法填充并获取填充的 [项对象](https://docs.scrapy.org/en/latest/topics/items.html#topics-items)。那是使用先前收集的数据（并使用输入处理器处理）调用输出处理器的时候。输出处理器的结果是分配给项目的最终值。

让我们看一个示例来说明如何为特定字段调用输入和输出处理器（这同样适用于任何其他字段）：

```python
l = ItemLoader(my_product.asitem(), some_selector)
l.default_output_processor = TakeFirst()
l.add_xpath("name", xpath1)  # (1)
l.add_xpath("name", xpath2)  # (2)
l.add_css("name", css)  # (3)
l.add_value("name", "test")  # (4)
return l.load_item()  # (5)
```

然后就可以使用 [使用项目加载器填充项目](# 使用项目加载器填充项目) 中的代码了

本库主推便捷，不太推荐使用以上代码自定义增加 `Item` 字段来适配 `Item Loaders` 的特性，除非某些场景下使用 `Item Loaders` 能够极大方便开发时，才推荐使用下。
