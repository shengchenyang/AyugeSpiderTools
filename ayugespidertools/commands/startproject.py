import argparse
from pathlib import Path

from scrapy.commands.startproject import Command

import ayugespidertools


class AyuCommand(Command):
    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        # To customize the file templates in TEMPLATES_TO_RENDER, override the
        # parent class's run method. See the commit history for an example.
        super().run(args, opts)
        # Add text hints to this library
        print(
            "Or you can start your first spider with ayuge:\n"
            "    ayuge genspider example example.com"
        )

    @property
    def templates_dir(self) -> str:
        assert self.settings is not None
        return str(
            Path(
                Path(ayugespidertools.__path__[0], "templates"),
                "project",
            )
        )
