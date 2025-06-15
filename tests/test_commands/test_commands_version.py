import argparse
from io import StringIO
from pathlib import Path

import toml

from ayugespidertools.commands.version import AyuCommand
from ayugespidertools.config import NormalConfig
from tests.test_commands.test_commands_crawl import TestProjectBase


def test_version():
    cmd = AyuCommand()
    namespace = argparse.Namespace()
    options = {"stdout": StringIO()}
    for key, value in options.items():
        setattr(namespace, key, value)

    cmd.run([], namespace)
    assert cmd.short_desc() == "Print AyugeSpiderTools version"


class TestVersionCommand(TestProjectBase):
    @staticmethod
    def _version() -> str:
        toml_file = Path(NormalConfig.ROOT_DIR, "pyproject.toml")
        conf = toml.load(toml_file)
        return conf["tool"]["poetry"]["version"]

    def test_output(self):
        _, out, _ = self.proc("version")
        assert out.strip() == f"AyugeSpiderTools {self._version()}"
