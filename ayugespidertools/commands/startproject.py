import argparse
from pathlib import Path

from scrapy.commands.startproject import Command

import ayugespidertools


class AyuCommand(Command):
    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        # 若想自定义 TEMPLATES_TO_RENDER 的文件模版，需重写父类的 run 方法，示例请查看提交历史
        super().run(args, opts)
        # 添加本库的文字提示内容
        print("Or you can start your first spider with ayuge:")
        print("    ayuge genspider example example.com")

    @property
    def templates_dir(self) -> str:
        assert self.settings is not None
        return str(
            Path(
                Path(ayugespidertools.__path__[0], "templates"),
                "project",
            )
        )
