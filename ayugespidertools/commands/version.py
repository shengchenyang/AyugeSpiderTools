from pathlib import Path

import toml
from scrapy.commands.version import Command

from ayugespidertools.config import NormalConfig


class AyuCommand(Command):
    def short_desc(self):
        return "Print AyugeSpiderTools version"

    def _version(self) -> str:
        toml_file = Path(NormalConfig.ROOT_DIR, "pyproject.toml")
        conf = toml.load(toml_file)
        return conf["tool"]["poetry"]["version"]

    def run(self, args, opts):
        print(f"AyugeSpiderTools {self._version()}")
