.PHONY: start clean build install build_dist test release pytest check

refresh: clean build install

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

start:
	pip install poetry
	poetry install
	pre-commit install

build:
	poetry build

install:
	$(PIPINSTALL)

build_dist:
	make clean
	python setup.py sdist bdist_wheel
	$(PIPINSTALL)
	make test

release:
	poetry publish

test:
	poetry install -E "all"
	coverage run -m pytest
	coverage combine
	coverage report
	make clean

pytest:
	poetry install
	pytest -W ignore::DeprecationWarning

check:
	pre-commit run --all-files

path = $(subst /,$(strip $(PATHSEP)),$1)

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
	-$(RM) $(call path, tests$(PATHSEP)docs$(PATHSEP)keys$(PATHSEP)localhost.crt)
	-$(RM) $(call path, tests$(PATHSEP)docs$(PATHSEP)keys$(PATHSEP)localhost.key)
	-$(RM) $(call path, tests$(PATHSEP)keys$(PATHSEP)localhost.crt)
	-$(RM) $(call path, tests$(PATHSEP)keys$(PATHSEP)localhost.key)
	poetry install
	pip uninstall -y ayugespidertools
