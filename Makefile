.PHONY: build build_dist check clean git help install patch pypi_token pytest major minor \
release start tag test version

refresh: clean build install

path = $(subst /,$(strip $(PATHSEP)),$1)
PROJECT_NAME = ayugespidertools

ifeq ($(OS),Windows_NT)
    RM = cmd.exe /C del /F /Q
    RMDIR = cmd.exe /C rd /S /Q
    PATHSEP = \\
    PIPINSTALL = cmd.exe /C "FOR %%i in (dist\*.whl) DO python -m pip install --no-index --no-deps %%i"
    CLEAN_PYCACHE = for /d /r . %%d in (__pycache__) do @(if exist "%%d" (rd /s /q "%%d"))
    CLEAN_PYTESTCACHE = for /d /r . %%d in (.pytest_cache) do @(if exist "%%d" (rd /s /q "%%d"))
    CLEAN_MYPYCACHE = for /d /r . %%d in (.mypy_cache) do @(if exist "%%d" (rd /s /q "%%d"))
else
    UNAME_S := $(shell uname -s 2>/dev/null || echo "unknown")
    ifeq ($(UNAME_S),Linux)
        RM = rm -f
        RMDIR = rm -rf
        PATHSEP = /
        PIPINSTALL = pip install dist/*.tar.gz
        CLEAN_PYCACHE = find . -type d -name '__pycache__' -print0 | xargs -0 rm -rf
        CLEAN_PYTESTCACHE = find . -type d -name '.pytest_cache' -print0 | xargs -0 rm -rf
        CLEAN_MYPYCACHE = find . -type d -name '.mypy_cache' -print0 | xargs -0 rm -rf
    endif
    ifeq ($(UNAME_S),Darwin)
        RM = rm -f
        RMDIR = rm -rf
        PATHSEP = /
        PIPINSTALL = pip install dist/*.tar.gz
        CLEAN_PYCACHE = find . -type d -name '__pycache__' -print0 | xargs -0 rm -rf
        CLEAN_PYTESTCACHE = find . -type d -name '.pytest_cache' -print0 | xargs -0 rm -rf
        CLEAN_MYPYCACHE = find . -type d -name '.mypy_cache' -print0 | xargs -0 rm -rf
    endif
endif

build:
	poetry build

build_dist:
	make clean
	python setup.py sdist bdist_wheel

check:
	poetry run pre-commit run --all-files
	poetry run mypy .
	poetry check

clean:
	-$(CLEAN_PYCACHE)
	-$(CLEAN_PYTESTCACHE)
	-$(CLEAN_MYPYCACHE)
	-$(RMDIR) $(call path, dist)
	-$(RMDIR) $(call path, file.log)
	-$(RMDIR) $(call path, docs$(PATHSEP)_build)
	-$(RMDIR) $(call path, htmlcov)
	-$(RM) $(call path, .coverage)
	-$(RM) $(call path, .coverage.*)
	-$(RM) $(call path, coverage.xml)
	-$(RMDIR) $(call path, .tox)
	-$(RM) $(call path, tests$(PATHSEP)docs$(PATHSEP)txt$(PATHSEP)run.log)
	-$(RM) $(call path, tests$(PATHSEP)keys$(PATHSEP)localhost.crt)
	-$(RM) $(call path, tests$(PATHSEP)keys$(PATHSEP)localhost.key)
	pip uninstall -y $(PROJECT_NAME)

git:
	git config core.eol lf
	git config core.autocrlf input
	git config core.safecrlf true
	git config --global http.proxy http://127.0.0.1:7897
	git config --global https.proxy http://127.0.0.1:7897

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build            Poetry build"
	@echo "  build_dist       Setuptools build"
	@echo "  check            Code check"
	@echo "  clean            Clean up test files, mypy cache and dist folders"
	@echo "  git              Set git proxy and line separator"
	@echo "  help             Show this help message"
	@echo "  install          Install whl/tar.gz file from the dist folder"
	@echo "  pypi_token       Set the poetry pypi-token, Run 'make pypi_token token=<token>' to set the poetry pypi_token"
	@echo "  pytest           Code test"
	@echo "  release          Publish package to PyPI:"
	@echo "                     1. Run 'make release token=<token>'"
	@echo "                     2. Run 'make release' if poetry pypi_token is already set"
	@echo "  start            Pre-development setup steps"
	@echo "  tag              Push a Git tag to trigger the publish action"
	@echo "  test             Code test and coverage report"
	@echo "  version          Shows the version of the project or bumps it when a valid bump rule is provided"
	@echo "                     1. Run 'make version' to get current project version"
	@echo "                     2. Run 'make version [patch|minor|major]' to bump version"

install:
	$(PIPINSTALL)

pypi_token:
	@echo "==> Setting up the poetry pypi-token..."
	@poetry config pypi-token.pypi $(token)
	@echo ":) Poetry pypi_token set successfully!"

pytest:
	poetry install -E "all"
	poetry run pytest -W ignore::DeprecationWarning

release:
	@if [ -n "$(token)" ]; then \
		make pypi_token token=$(token); \
	else \
		echo "Please ensure the pypi-token is configured!"; \
	fi
	@echo "==> Publishing package to PyPI..."
	poetry publish
	@echo ":) Publish successfully"

start:
	pyenv local 3.9.20
	pip install poetry==2.1.1
	poetry config virtualenvs.in-project true
	poetry self add poetry-bumpversion
	poetry env use python
	poetry install -E "all"
	poetry run pre-commit install

tag:
	@PKG_VER=$(shell poetry version --short); \
	TAG_NAME="$(PROJECT_NAME)-$${PKG_VER}"; \
	echo "==> Creating tag $$TAG_NAME"; \
	git tag $$TAG_NAME; \
	git push origin $$TAG_NAME

test:
	poetry install -E "all"
	poetry run coverage run -m pytest
	poetry run coverage combine
	poetry run coverage report

version:
	@if [ "$(filter patch minor major,$(MAKECMDGOALS))" = "" ]; then \
		poetry version; \
	else \
		poetry version $(filter patch minor major,$(MAKECMDGOALS)); \
	fi

patch:
	@:

minor:
	@:

major:
	@:
