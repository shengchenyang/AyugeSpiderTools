from scrapy.commands.version import Command

from ayugespidertools import __version__


class AyuCommand(Command):
    def short_desc(self):
        return "Print AyugeSpiderTools version"

    def run(self, args, opts):
        print(f"AyugeSpiderTools {__version__}")
