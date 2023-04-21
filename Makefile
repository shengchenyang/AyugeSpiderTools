.PHONY: clean build install build_dist test release

ifeq ($(OS),Windows_NT)
    RM = cmd.exe /C del /F /Q
    RMDIR = cmd.exe /C rd /S /Q
    PATHSEP = \\
    PIPINSTALL = cmd.exe /C "FOR %%i in (dist\*.whl) DO python -m pip install --no-index --no-deps %%i"
else
    UNAME_S := $(shell uname -s 2>/dev/null || echo "unknown")
    ifeq ($(UNAME_S),Linux)
        RM = rm -f
        RMDIR = rm -rf
        PATHSEP = /
        PIPINSTALL = pip install dist/*.tar.gz
    endif
    ifeq ($(UNAME_S),Darwin)
        RM = rm -f
        RMDIR = rm -rf
        PATHSEP = /
        PIPINSTALL = pip install dist/*.tar.gz
    endif
endif

start:
	pip install poetry
	poetry install

build:
	poetry build

install:
	make clean
	make build
	$(PIPINSTALL)

build_dist:
	make clean
	python setup.py sdist bdist_wheel
	$(PIPINSTALL)
	make test

release:
	poetry publish

test:
	poetry install
	coverage run -m pytest
	coverage combine
	coverage report
	make clean

pytest:
	poetry install
	pytest -W ignore::DeprecationWarning


path = $(subst /,$(strip $(PATHSEP)),$1)

clean:
	-$(RMDIR) $(call path,.pytest_cache)
	-$(RMDIR) $(call path,ayugespidertools$(PATHSEP)__pycache__)
	-$(RMDIR) $(call path,ayugespidertools$(PATHSEP)common$(PATHSEP)__pycache__)
	-$(RMDIR) $(call path,ayugespidertools$(PATHSEP)scraper$(PATHSEP)__pycache__)
	-$(RMDIR) $(call path,dist)
	-$(RMDIR) $(call path,docs$(PATHSEP)_build)
	-$(RMDIR) $(call path,htmlcov)
	-$(RMDIR) $(call path,tests$(PATHSEP)__pycache__)
	-$(RMDIR) $(call path,tests$(PATHSEP).pytest_cache)
	-$(RMDIR) $(call path,tests$(PATHSEP)test_commands$(PATHSEP).pytest_cache)
	-$(RMDIR) $(call path,tests$(PATHSEP)test_common$(PATHSEP).pytest_cache)
	-$(RM) $(call path,.coverage)
	-$(RM) $(call path,.coverage.*)
	-$(RM) $(call path,coverage.xml)
	-$(RMDIR) $(call path,.tox)
	-$(RM) $(call path,tests$(PATHSEP)docs$(PATHSEP)txt$(PATHSEP)run.log)
	-$(RMDIR) $(call path,tests$(PATHSEP)docs$(PATHSEP)keys$(PATHSEP)__pycache__)
	-$(RMDIR) $(call path,tests$(PATHSEP)docs$(PATHSEP)keys$(PATHSEP)localhost.crt)
	-$(RMDIR) $(call path,tests$(PATHSEP)docs$(PATHSEP)keys$(PATHSEP)localhost.key)
	pip uninstall -y ayugespidertools
