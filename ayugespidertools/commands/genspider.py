from pathlib import Path

from scrapy.commands.genspider import Command

import ayugespidertools


class AyuCommand(Command):
    @property
    def templates_dir(self) -> str:
        assert self.settings is not None
        return str(
            Path(
                Path(ayugespidertools.__path__[0], "templates"),
                "spiders",
            )
        )
