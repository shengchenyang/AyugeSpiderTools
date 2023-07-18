from scrapy.commands.crawl import Command


class AyuCommand(Command):
    """完全 copy 继承 scrapy 中的方法
    不推荐使用 ayuge crawl 来执行 spider，没必要，还是使用 scrapy crawl 吧
    """

    ...
