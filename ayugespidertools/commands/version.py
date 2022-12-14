import configparser
from scrapy.commands.genspider import Command
from ayugespidertools.config import NormalConfig


class AyuCommand(Command):

    def short_desc(self):
        return "Print AyugeSpiderTools version"

    def run(self, args, opts):
        config_parse = configparser.ConfigParser()
        config_parse.read(f"{NormalConfig.ROOT_DIR}/pyproject.toml", encoding="utf-8")
        version = config_parse["tool.poetry"]["version"]
        print(f"AyugeSpiderTools {version}")
