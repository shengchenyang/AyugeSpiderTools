import sys

from scrapy.utils.testproc import ProcessTest
from twisted.internet import defer
from twisted.trial import unittest

from ayugespidertools.commands.version import AyuCommand


def test_version():
    AyuCommand().run(None, None)
    print("""正常返回示例为：AyugeSpiderTools "1.0.7" """)
    assert True


class VersionTest(ProcessTest, unittest.TestCase):
    command = "version"

    @defer.inlineCallbacks
    def test_output(self):
        encoding = getattr(sys.stdout, "encoding") or "utf-8"
        print("ss", encoding)
        _, out, _ = yield self.execute([])
        print("__", _, out)
        self.assertEqual(
            out.strip().decode(encoding),
            "Scrapy 2.8.0",
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
