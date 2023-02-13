import configparser

from scrapy.commands.version import Command

from ayugespidertools.config import NormalConfig


class AyuCommand(Command):
    default_settings = {"LOG_ENABLED": False, "SPIDER_LOADER_WARN_ONLY": True}

    def short_desc(self):
        return "Print AyugeSpiderTools version"

    @staticmethod
    def version():
        config_parser = configparser.ConfigParser()
        config_parser.read(f"{NormalConfig.ROOT_DIR}/pyproject.toml", encoding="utf-8")
        return config_parser["tool.poetry"]["version"][1:-1]

    def run(self, args, opts):
        print(f"AyugeSpiderTools {AyuCommand.version()}")
