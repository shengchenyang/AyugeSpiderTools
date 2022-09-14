import ayugespidertools
from scrapy.commands.genspider import Command


class AyuCommand(Command):

    def short_desc(self):
        return "Print AyugeSpiderTools version"

    def run(self, args, opts):
        print(f"AyugeSpiderTools {ayugespidertools.__version__}")
