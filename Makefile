.PHONY: build build_dist check clean format git help install patch pytest major minor \
release start tag tag_remove test version

refresh: clean build install

path = $(subst /,$(strip $(PATHSEP)),$1)
PROJECT_NAME = ayugespidertools

ifeq ($(OS),Windows_NT)
    RM = cmd.exe /C del /F /Q
    RMDIR = cmd.exe /C rd /S /Q
    PATHSEP = \\
    PIPINSTALL = cmd.exe /C "FOR %%i in (dist\*.whl) DO uv pip install --no-index --no-deps %%i"
    CLEAN_PYCACHE = for /d /r . %%d in (__pycache__) do @(if exist "%%d" (rd /s /q "%%d"))
    CLEAN_PYTESTCACHE = for /d /r . %%d in (.pytest_cache) do @(if exist "%%d" (rd /s /q "%%d"))
    CLEAN_MYPYCACHE = for /d /r . %%d in (.mypy_cache) do @(if exist "%%d" (rd /s /q "%%d"))
else
    UNAME_S := $(shell uname -s 2>/dev/null || echo "unknown")
    ifeq ($(UNAME_S),Linux)
        RM = rm -f
        RMDIR = rm -rf
        PATHSEP = /
        PIPINSTALL = uv pip install dist/*.tar.gz
        CLEAN_PYCACHE = find . -type d -name '__pycache__' -print0 | xargs -0 rm -rf
        CLEAN_PYTESTCACHE = find . -type d -name '.pytest_cache' -print0 | xargs -0 rm -rf
        CLEAN_MYPYCACHE = find . -type d -name '.mypy_cache' -print0 | xargs -0 rm -rf
    endif
    ifeq ($(UNAME_S),Darwin)
        RM = rm -f
        RMDIR = rm -rf
        PATHSEP = /
        PIPINSTALL = uv pip install dist/*.tar.gz
        CLEAN_PYCACHE = find . -type d -name '__pycache__' -print0 | xargs -0 rm -rf
        CLEAN_PYTESTCACHE = find . -type d -name '.pytest_cache' -print0 | xargs -0 rm -rf
        CLEAN_MYPYCACHE = find . -type d -name '.mypy_cache' -print0 | xargs -0 rm -rf
    endif
endif

build:
	uv build --no-create-gitignore

build_dist:
	make clean
	python setup.py sdist bdist_wheel

check:
	uv run pre-commit run --all-files
	uv run mypy .
	uv run ruff check --fix

clean:
	-$(CLEAN_PYCACHE)
	-$(CLEAN_PYTESTCACHE)
	-$(CLEAN_MYPYCACHE)
	-$(RMDIR) $(call path, .tox)
	-$(RMDIR) $(call path, .tox_envs)
	-$(RMDIR) $(call path, dist)
	-$(RMDIR) $(call path, file.log)
	-$(RMDIR) $(call path, docs$(PATHSEP)_build)
	-$(RMDIR) $(call path, htmlcov)
	-$(RM) $(call path, .coverage)
	-$(RM) $(call path, .coverage.*)
	-$(RM) $(call path, coverage.xml)
	-$(RM) $(call path, tests$(PATHSEP)docs$(PATHSEP)txt$(PATHSEP)run.log)
	-$(RM) $(call path, tests$(PATHSEP)keys$(PATHSEP)localhost.crt)
	-$(RM) $(call path, tests$(PATHSEP)keys$(PATHSEP)localhost.key)
	uv pip uninstall $(PROJECT_NAME)

format:
	- uv run ruff format
	- uv run ruff check --fix

git:
	git config core.eol lf
	git config core.autocrlf input
	git config core.safecrlf true
	git config --global http.proxy http://127.0.0.1:7897
	git config --global https.proxy http://127.0.0.1:7897

help:
	@echo "Usage: make [target] [option]"
	@echo ""
	@echo "Targets:"
	@echo "  build            Uv build"
	@echo "  build_dist       Setuptools build"
	@echo "  check            Code check"
	@echo "  clean            Clean up test files, mypy cache and dist folders"
	@echo "  git              Set git proxy and line separator"
	@echo "  format           Code format"
	@echo "  help             Show this help message"
	@echo "  install          Install whl/tar.gz file from the dist folder"
	@echo "  pytest           Code test"
	@echo "  release          Publish package to PyPI"
	@echo "  start            Pre-development setup steps"
	@echo "  tag              Push a Git tag to trigger the publish action"
	@echo "  tag_remove       Delete current (Git and Local) tag if the publish Action fails"
	@echo "  test             Code test and coverage report"
	@echo "  version          Shows the version of the project or bumps it when a valid bump rule is provided"
	@echo "                     1. Run 'make version' to get current project version"
	@echo "                     2. Run 'make version [patch|minor|major]' to bump version"

install:
	$(PIPINSTALL)

pytest:
	uv sync --all-extras --all-groups
	uv run pytest -W ignore::DeprecationWarning

release:
	uv publish
	@echo ":) Publish successfully"

start:
	uv sync --python 3.10.11 --all-extras --all-groups
	uv run pre-commit install

tag:
	@PKG_VER=$(shell uv version --short); \
	TAG_NAME="$(PROJECT_NAME)-$${PKG_VER}"; \
	echo "==> Creating tag $$TAG_NAME"; \
	git tag $$TAG_NAME; \
	git push origin $$TAG_NAME

tag_remove:
	@PKG_VER=$(shell uv version --short); \
	TAG_NAME="$(PROJECT_NAME)-$${PKG_VER}"; \
	echo "==> Deleting tag $$TAG_NAME"; \
	git tag -d $$TAG_NAME; \
	git push origin :refs/tags/$$TAG_NAME

test:
	uv sync --all-extras --all-groups
	uv run coverage run -m pytest
	uv run coverage combine
	uv run coverage report

version:
	@if [ "$(filter patch minor major,$(MAKECMDGOALS))" = "" ]; then \
		uv version; \
	else \
		uv run bump-my-version bump $(filter patch minor major,$(MAKECMDGOALS)); \
	fi

patch:
	@:

minor:
	@:

major:
	@:
