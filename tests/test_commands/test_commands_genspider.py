import os
from pathlib import Path

from scrapy.settings import Settings

from ayugespidertools.commands.genspider import AyuCommand
from tests.test_commands.test_commands_crawl import TestProjectBase


class TestCommandBase(TestProjectBase):
    def setup_method(self):
        super().setup_method()
        self.call("startproject", self.project_name)
        self.cwd = self.proj_path
        self.env["SCRAPY_SETTINGS_MODULE"] = f"{self.project_name}.settings"


class TestGenspiderCommand(TestCommandBase):
    def test_arguments(self):
        # only pass one argument. spider script shouldn't be created
        assert self.call("genspider", "test_name") == 2
        assert not Path(self.proj_mod_path, "spiders", "test_name.py").exists()
        # pass two arguments <name> <domain>. spider script should be created
        assert self.call("genspider", "test_name", "test.com") == 0
        assert Path(self.proj_mod_path, "spiders", "test_name.py").exists()

    def test_template(self, tplname="crawl"):
        args = [f"--template={tplname}"] if tplname else []
        spname = "test_spider"
        spmodule = f"{self.project_name}.spiders.{spname}"
        p, out, err = self.proc("genspider", spname, "test.com", *args)
        assert (
            f"Created spider {spname!r} using template {tplname!r} in module:{os.linesep}  {spmodule}"
            in out
        )
        assert Path(self.proj_mod_path, "spiders", "test_spider.py").exists()
        modify_time_before = (
            Path(self.proj_mod_path, "spiders", "test_spider.py").stat().st_mtime
        )
        p, out, err = self.proc("genspider", spname, "test.com", *args)
        assert f"Spider {spname!r} already exists in module" in out
        modify_time_after = (
            Path(self.proj_mod_path, "spiders", "test_spider.py").stat().st_mtime
        )
        assert modify_time_after == modify_time_before

    def test_template_basic(self):
        self.test_template(tplname="basic")

    def test_template_async(self):
        self.test_template(tplname="async")

    def test_template_csvfeed(self):
        self.test_template(tplname="csvfeed")

    def test_template_xmlfeed(self):
        self.test_template(tplname="xmlfeed")

    def test_genspider_command_object(self):
        cmd = AyuCommand()
        cmd.settings = Settings()
        templates_dir = cmd.templates_dir
        assert isinstance(templates_dir, str)
        assert "ayugespidertools" in templates_dir
        assert "templates" in templates_dir
