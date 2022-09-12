from os.path import join, exists, abspath
import ayugespidertools
from scrapy.commands.startproject import Command


class AyuCommand(Command):

    def run(self, *args, **kwargs):
        super(AyuCommand, self).run(*args, **kwargs)
        print("Or you can start your first spider with ayugespidertools:")
        print("    ayugespidertools genspider example example.com")

    @property
    def templates_dir(self):
        return join(join(ayugespidertools.__path__[0], 'templates'), 'project')
