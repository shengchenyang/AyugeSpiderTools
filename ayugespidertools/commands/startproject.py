import string
from pathlib import Path
from shutil import ignore_patterns, move

from scrapy.commands.startproject import Command
from scrapy.exceptions import UsageError
from scrapy.utils.template import render_templatefile, string_camelcase

import ayugespidertools
from ayugespidertools.common.params import Param

# 添加需要的自定义配置文件
TEMPLATES_TO_RENDER = (
    ("pyproject.toml",),
    ("README.md",),
    ("requirements.txt",),
    ("scrapy.cfg",),
    ("${project_name}", "settings.py.tmpl"),
    ("${project_name}", "items.py.tmpl"),
    ("${project_name}", "pipelines.py.tmpl"),
    ("${project_name}", "middlewares.py.tmpl"),
    # 添加 run.py 总运行文件
    ("${project_name}", "run.py.tmpl"),
)

IGNORE = ignore_patterns("*.pyc", "__pycache__", ".svn")


class AyuCommand(Command):
    def run(self, args, opts):
        if len(args) not in (1, 2):
            raise UsageError()

        project_name = args[0]

        if len(args) == 2:
            _has_project_dir_args = True
            project_dir = Path(args[1])
        else:
            _has_project_dir_args = False
            project_dir = Path(args[0])

        if (project_dir / "scrapy.cfg").exists():
            self.exitcode = 1
            print(f"Error: scrapy.cfg already exists in {project_dir.resolve()}")
            return

        if not self._is_valid_name(project_name):
            self.exitcode = 1
            return

        self._copytree(Path(self.templates_dir), project_dir.resolve())
        move(project_dir / "module", project_dir / project_name)
        for paths in TEMPLATES_TO_RENDER:
            tplfile = Path(
                project_dir,
                *(
                    string.Template(s).substitute(project_name=project_name)
                    for s in paths
                ),
            )
            render_templatefile(
                tplfile,
                project_name=project_name,
                ProjectName=string_camelcase(project_name),
            )

        # 添加执行 shell 文件 run.sh 的生成
        if _has_project_dir_args:
            run_shell_path = f"{project_dir}/{project_name}/run.sh.tmpl"
        else:
            run_shell_path = f"{project_dir}/{project_dir}/run.sh.tmpl"
        run_shell_abspath = Path(project_dir).resolve()
        # 如果是 windows 环境的话，就不生成 shell 文件了，没啥必要
        if Param.IS_WINDOWS:
            print("Info: The run.sh file is no longer generated under windows.")
            del_file = Path(run_shell_path)
            if Path.exists(del_file):
                del_file.unlink()

        else:
            render_templatefile(
                run_shell_path,
                project_startup_dir=run_shell_abspath,
                ProjectStartupDir=string_camelcase(str(run_shell_abspath)),
                project_name=project_name,
                ProjectName=string_camelcase(project_name),
            )

        print(
            f"New Scrapy project '{project_name}', using template directory "
            f"'{self.templates_dir}', created in:"
        )
        print(f"    {project_dir.resolve()}\n")
        print("You can start your first spider with:")
        print(f"    cd {project_dir}")
        print("    scrapy genspider example example.com")
        # 添加本库的文字提示内容
        print("Or you can start your first spider with ayuge:")
        print("    ayuge genspider example example.com")

    @property
    def templates_dir(self) -> str:
        # 修改 startproject 模板文件路径为 ayugespidertools 的自定义路径
        return str(
            Path(
                Path(ayugespidertools.__path__[0], "templates"),
                "project",
            )
        )
