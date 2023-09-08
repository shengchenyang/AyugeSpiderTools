import sys
from io import StringIO

from scrapy.utils.testproc import ProcessTest
from twisted.internet import defer
from twisted.trial import unittest

from ayugespidertools.commands.version import AyuCommand


def test_version():
    cmd = AyuCommand()
    output = StringIO()
    cmd.run([], {"stdout": output})
    assert cmd.short_desc() == "Print AyugeSpiderTools version"


class VersionTest(ProcessTest, unittest.TestCase):
    command = "version"

    @defer.inlineCallbacks
    def test_output(self):
        encoding = getattr(sys.stdout, "encoding") or "utf-8"
        _, out, _ = yield self.execute([])
        self.assertEqual(
            out.strip().decode(encoding),
            "Scrapy 2.10.1",
        )

    @defer.inlineCallbacks
    def test_verbose_output(self):
        encoding = getattr(sys.stdout, "encoding") or "utf-8"
        _, out, _ = yield self.execute(["-v"])
        headers = [
            line.partition(":")[0].strip()
            for line in out.strip().decode(encoding).splitlines()
        ]
        self.assertEqual(
            headers,
            [
                "Scrapy",
                "lxml",
                "libxml2",
                "cssselect",
                "parsel",
                "w3lib",
                "Twisted",
                "Python",
                "pyOpenSSL",
                "cryptography",
                "Platform",
            ],
        )
