import os
from pathlib import Path

# sourcery skip: dont-import-test-modules
from tests.test_commands.test_commands_crawl import ProjectTest


class CommandTest(ProjectTest):
    def setUp(self):
        super().setUp()
        self.call("startproject", self.project_name)
        self.cwd = Path(self.temp_path, self.project_name)
        self.env["SCRAPY_SETTINGS_MODULE"] = f"{self.project_name}.settings"


class GenspiderCommandTest(CommandTest):
    def test_arguments(self):
        # only pass one argument. spider script shouldn't be created
        self.assertEqual(2, self.call("genspider", "test_name"))
        assert not Path(self.proj_mod_path, "spiders", "test_name.py").exists()
        # pass two arguments <name> <domain>. spider script should be created
        self.assertEqual(0, self.call("genspider", "test_name", "test.com"))
        assert Path(self.proj_mod_path, "spiders", "test_name.py").exists()

    def test_template(self, tplname="crawl"):
        args = [f"--template={tplname}"] if tplname else []
        spname = "test_spider"
        spmodule = f"{self.project_name}.spiders.{spname}"
        p, out, err = self.proc("genspider", spname, "test.com", *args)
        self.assertIn(
            f"Created spider {spname!r} using template {tplname!r} in module:{os.linesep}  {spmodule}",
            out,
        )
        self.assertTrue(Path(self.proj_mod_path, "spiders", "test_spider.py").exists())
        modify_time_before = (
            Path(self.proj_mod_path, "spiders", "test_spider.py").stat().st_mtime
        )
        p, out, err = self.proc("genspider", spname, "test.com", *args)
        self.assertIn(f"Spider {spname!r} already exists in module", out)
        modify_time_after = (
            Path(self.proj_mod_path, "spiders", "test_spider.py").stat().st_mtime
        )
        self.assertEqual(modify_time_after, modify_time_before)

    def test_template_basic(self):
        self.test_template(tplname="basic")

    def test_template_async(self):
        self.test_template(tplname="async")

    def test_template_csvfeed(self):
        self.test_template(tplname="csvfeed")

    def test_template_xmlfeed(self):
        self.test_template(tplname="xmlfeed")
