from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryFile, mkdtemp
from threading import Timer
from typing import Any

from scrapy.utils.python import to_unicode
from scrapy.utils.test import get_testenv


class TestProjectBase:
    project_name = "testproject"

    def setup_method(self):
        self.temp_path = mkdtemp()
        self.cwd = self.temp_path
        self.proj_path = Path(self.temp_path, self.project_name)
        self.proj_mod_path = self.proj_path / self.project_name
        self.env = get_testenv()

    def teardown_method(self):
        rmtree(self.temp_path)

    def call(self, *args: str, **popen_kwargs: Any) -> int:
        with TemporaryFile() as out:
            args = (sys.executable, "-m", "ayugespidertools.utils.cmdline", *args)
            return subprocess.call(
                args, stdout=out, stderr=out, cwd=self.cwd, env=self.env, **popen_kwargs
            )

    def proc(
        self, *args: str, **popen_kwargs: Any
    ) -> tuple[subprocess.Popen[bytes], str, str]:
        args = (sys.executable, "-m", "ayugespidertools.utils.cmdline", *args)
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
            raise AssertionError("Command took too much time to complete")

        timer = Timer(15, kill_proc)
        try:
            timer.start()
            stdout, stderr = p.communicate()
            stderr = str(stderr)
        finally:
            timer.cancel()

        return p, to_unicode(stdout), to_unicode(stderr)

    def find_in_file(self, filename: str | os.PathLike, regex) -> re.Match | None:
        """Find first pattern occurrence in file"""
        pattern = re.compile(regex)
        with Path(filename).open("r", encoding="utf-8") as f:
            for line in f:
                match = pattern.search(line)
                if match is not None:
                    return match
        return None


class TestCommandBase(TestProjectBase):
    def setup_method(self):
        super().setup_method()
        self.call("startproject", self.project_name)
        self.cwd = self.proj_path
        self.env["SCRAPY_SETTINGS_MODULE"] = f"{self.project_name}.settings"


class TestCrawlCommand(TestCommandBase):
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

    async def start(self):
        self.logger.debug("It works!")
        return
        yield
"""
        log = self.get_log(spider_code)
        assert "[myspider] DEBUG: It works!" in log
