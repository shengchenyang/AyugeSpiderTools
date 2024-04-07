import sys
from io import StringIO
from pathlib import Path

import toml
from scrapy.utils.testproc import ProcessTest
from twisted.internet import defer
from twisted.trial import unittest

from ayugespidertools.commands.version import AyuCommand
from ayugespidertools.config import NormalConfig

ProcessTest.prefix = [sys.executable, "-m", "ayugespidertools.utils.cmdline"]


def test_version():
    cmd = AyuCommand()
    output = StringIO()
    cmd.run([], {"stdout": output})
    assert cmd.short_desc() == "Print AyugeSpiderTools version"


class VersionTest(ProcessTest, unittest.TestCase):
    command = "version"

    @staticmethod
    def _version() -> str:
        toml_file = Path(NormalConfig.ROOT_DIR, "pyproject.toml")
        conf = toml.load(toml_file)
        return conf["tool"]["poetry"]["version"]

    @defer.inlineCallbacks
    def test_output(self):
        encoding = getattr(sys.stdout, "encoding") or "utf-8"
        _, out, _ = yield self.execute([])
        self.assertEqual(
            out.strip().decode(encoding),
            f"AyugeSpiderTools {self._version()}",
        )
