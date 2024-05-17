import argparse
from typing import List

from scrapy.commands.version import Command

from ayugespidertools import __version__


class AyuCommand(Command):
    def short_desc(self) -> str:
        return "Print AyugeSpiderTools version"

    def run(self, args: List[str], opts: argparse.Namespace) -> None:
        print(f"AyugeSpiderTools {__version__}")
