from pathlib import Path

from scrapy.commands.genspider import Command

import ayugespidertools


class AyuCommand(Command):
    @property
    def templates_dir(self) -> str:
        assert self.settings is not None
        templates_dir = self.settings["TEMPLATES_DIR"]
        if self.settings.getpriority("TEMPLATES_DIR") == 0:
            templates_dir = Path(ayugespidertools.__path__[0], "templates")
        return str(Path(templates_dir, "spiders"))
