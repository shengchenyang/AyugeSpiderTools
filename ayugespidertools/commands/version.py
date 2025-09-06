from __future__ import annotations

from typing import TYPE_CHECKING

from scrapy.commands.version import Command

from ayugespidertools import __version__

if TYPE_CHECKING:
    import argparse


class AyuCommand(Command):
    def short_desc(self) -> str:
        return "Print AyugeSpiderTools version"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        print(f"AyugeSpiderTools {__version__}")
