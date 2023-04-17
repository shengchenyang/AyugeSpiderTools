import toml
from scrapy.commands.version import Command

from ayugespidertools.config import NormalConfig


class AyuCommand(Command):
    def short_desc(self):
        return "Print AyugeSpiderTools version"

    def _version(self) -> str:
        with open(
            f"{NormalConfig.ROOT_DIR}/pyproject.toml", "r", encoding="utf-8"
        ) as f:
            config = toml.load(f)

        return config["tool"]["poetry"]["version"]

    def run(self, args, opts):
        print(f"AyugeSpiderTools {self._version()}")
