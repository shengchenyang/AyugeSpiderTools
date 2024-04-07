import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from threading import Timer
from typing import Optional, Union

from scrapy.utils.python import to_unicode
from scrapy.utils.test import get_testenv
from twisted.trial import unittest


class ProjectTest(unittest.TestCase):
    project_name = "testproject"

    def setUp(self):
        self.temp_path = mkdtemp()
        self.cwd = self.temp_path
        self.proj_path = Path(self.temp_path, self.project_name)
        self.proj_mod_path = self.proj_path / self.project_name
        self.env = get_testenv()

    def tearDown(self):
        rmtree(self.temp_path)

    def call(self, *new_args, **kwargs):
        with tempfile.TemporaryFile() as out:
            args = (sys.executable, "-m", "ayugespidertools.utils.cmdline") + new_args
            return subprocess.call(
                args, stdout=out, stderr=out, cwd=self.cwd, env=self.env, **kwargs
            )

    def proc(self, *new_args, **popen_kwargs):
        args = (sys.executable, "-m", "ayugespidertools.utils.cmdline") + new_args
        p = subprocess.Popen(
            args,
            cwd=popen_kwargs.pop("cwd", self.cwd),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **popen_kwargs,
        )

        def kill_proc():
            p.kill()
            p.communicate()
            assert False, "Command took too much time to complete"

        timer = Timer(15, kill_proc)
        try:
            timer.start()
            stdout, stderr = p.communicate()
            stderr = str(stderr)
        finally:
            timer.cancel()

        return p, to_unicode(stdout), to_unicode(stderr)

    def find_in_file(
        self, filename: Union[str, os.PathLike], regex
    ) -> Optional[re.Match]:
        """Find first pattern occurrence in file"""
        pattern = re.compile(regex)
        with Path(filename).open("r", encoding="utf-8") as f:
            for line in f:
                match = pattern.search(line)
                if match is not None:
                    return match
        return None


class CommandTest(ProjectTest):
    def setUp(self):
        super().setUp()
        self.call("startproject", self.project_name)
        self.cwd = Path(self.temp_path, self.project_name)
        self.env["SCRAPY_SETTINGS_MODULE"] = f"{self.project_name}.settings"


class CrawlCommandTest(CommandTest):
    def crawl(self, code, args=()):
        Path(self.proj_mod_path, "spiders", "myspider.py").write_text(
            code, encoding="utf-8"
        )
        return self.proc("crawl", "myspider", *args)

    def get_log(self, code, args=()):
        _, _, stderr = self.crawl(code, args=args)
        stderr = str(stderr)
        return stderr

    def test_no_output(self):
        spider_code = """
from ayugespidertools.spiders import AyuSpider

class MySpider(AyuSpider):
    name = "myspider"
    custom_settings = {
        "LOGURU_ENABLED": False,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": None,
    }

    def start_requests(self):
        self.logger.debug("It works!")
        return []
"""
        log = self.get_log(spider_code)
        self.assertIn("[myspider] DEBUG: It works!", log)
