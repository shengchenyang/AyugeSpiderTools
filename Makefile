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
	pytest -W ignore::DeprecationWarning tests/test_MysqlClient.py


path = $(subst /,$(strip $(PATHSEP)),$1)

clean:
	-$(RMDIR) $(call path,.pytest_cache)
	-$(RMDIR) $(call path,tests$(PATHSEP)__pycache__)
	-$(RMDIR) $(call path,tests$(PATHSEP).pytest_cache)
	-$(RMDIR) $(call path,dist)
	pip uninstall -y ayugespidertools
