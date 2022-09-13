from os.path import join, dirname, abspath, exists, splitext
import ayugespidertools
from scrapy.commands.genspider import Command


class AyuCommand(Command):

    @property
    def templates_dir(self):
        return join(
            join(ayugespidertools.__path__[0], 'templates'),
            'spiders'
        )
