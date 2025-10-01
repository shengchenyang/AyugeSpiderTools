import sys
from pathlib import Path
from tempfile import mkdtemp

from scrapy.settings import Settings

from ayugespidertools.commands.startproject import AyuCommand
from tests.test_commands.test_commands_crawl import TestProjectBase


class TestStartprojectCommand(TestProjectBase):
    def test_startproject(self):
        p, out, err = self.proc("startproject", self.project_name)
        print(out)
        print(err, file=sys.stderr)
        assert p.returncode == 0

        assert Path(self.proj_path, "scrapy.cfg").exists()
        assert Path(self.proj_path, "testproject").exists()
        assert Path(self.proj_mod_path, "__init__.py").exists()
        assert Path(self.proj_mod_path, "items.py").exists()
        assert Path(self.proj_mod_path, "pipelines.py").exists()
        assert Path(self.proj_mod_path, "settings.py").exists()
        assert Path(self.proj_mod_path, "spiders", "__init__.py").exists()

        assert self.call("startproject", self.project_name) == 1
        assert self.call("startproject", "wrong---project---name") == 1
        assert self.call("startproject", "sys") == 1

    def test_startproject_with_project_dir(self):
        project_dir = mkdtemp()
        assert self.call("startproject", self.project_name, project_dir) == 0

        assert Path(project_dir, "scrapy.cfg").exists()
        assert Path(project_dir, "testproject").exists()
        assert Path(project_dir, self.project_name, "__init__.py").exists()
        assert Path(project_dir, self.project_name, "items.py").exists()
        assert Path(project_dir, self.project_name, "pipelines.py").exists()
        assert Path(project_dir, self.project_name, "settings.py").exists()
        assert Path(project_dir, self.project_name, "spiders", "__init__.py").exists()

        assert self.call("startproject", self.project_name, project_dir + "2") == 0

        assert self.call("startproject", self.project_name, project_dir) == 1
        assert self.call("startproject", self.project_name + "2", project_dir) == 1
        assert self.call("startproject", "wrong---project---name") == 1
        assert self.call("startproject", "sys") == 1
        assert self.call("startproject") == 2
        assert (
            self.call("startproject", self.project_name, project_dir, "another_params")
            == 2
        )

    def test_existing_project_dir(self):
        project_dir = mkdtemp()
        project_name = self.project_name + "_existing"
        project_path = Path(project_dir, project_name)
        project_path.mkdir()

        p, out, err = self.proc("startproject", project_name, cwd=project_dir)
        print(out)
        print(err, file=sys.stderr)
        assert p.returncode == 0

        assert Path(project_path, "scrapy.cfg").exists()
        assert Path(project_path, project_name).exists()
        assert Path(project_path, project_name, "__init__.py").exists()
        assert Path(project_path, project_name, "items.py").exists()
        assert Path(project_path, project_name, "pipelines.py").exists()
        assert Path(project_path, project_name, "settings.py").exists()
        assert Path(project_path, project_name, "spiders", "__init__.py").exists()

    def test_err_project_name(self):
        project_name = f"123{self.project_name}"
        p, out, err = self.proc("startproject", project_name)
        print(out)
        print(err, file=sys.stderr)
        assert p.returncode == 1

    def test_startproject_command_object(self):
        cmd = AyuCommand()
        cmd.settings = Settings()
        templates_dir = cmd.templates_dir
        assert isinstance(templates_dir, str)
        assert "ayugespidertools" in templates_dir
        assert "templates" in templates_dir
        assert "project" in templates_dir
