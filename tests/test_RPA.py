import shutil
from pathlib import Path

import pytest

from ayugespidertools.RPA import AboutPyppeteer
from tests import tests_dir


@pytest.fixture(scope="module")
def run_log_need():
    src_file = f"{tests_dir}/docs/txt/run_temp.log"
    dst_file = f"{tests_dir}/docs/txt/run.log"
    _dst_file = Path(dst_file)
    if Path.exists(_dst_file):
        _dst_file.unlink()
    shutil.copy(src_file, dst_file)


def test_get_crawl_debug(run_log_need):
    with open(f"{tests_dir}/docs/txt/run.log", "r", encoding="utf-8") as f:
        content = f.read()
    num = AboutPyppeteer.get_crawl_debug(content=content)
    assert num == 11


@pytest.mark.skip()
def test_quit_process(run_log_need):
    # 暂时不测试此功能
    AboutPyppeteer.quit_process(process_name="curr_spider", sudo_pwd="root")


@pytest.mark.skip()
def test_deal_pyppeteer_suspend(run_log_need):
    # 暂时不测试此功能
    AboutPyppeteer.deal_pyppeteer_suspend(fn=f"{tests_dir}/docs/txt/run.log", line=1)
    AboutPyppeteer.deal_pyppeteer_suspend(fn=f"{tests_dir}/docs/txt/run.log", line=4)
