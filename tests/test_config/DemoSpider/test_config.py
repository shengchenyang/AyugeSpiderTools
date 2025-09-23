import os

import pytest

from ayugespidertools.config import get_cfg


@pytest.fixture
def change_test_directory():
    # 保存当前工作目录
    original_dir = os.getcwd()
    new_test_dir = os.path.join(os.path.dirname(__file__))

    try:
        # 切换到 test_config 的工作目录
        os.chdir(new_test_dir)
        yield
    finally:
        # 测试完成后恢复工作目录
        os.chdir(original_dir)


def test_default_settings(change_test_directory):
    cfg = get_cfg()
    assert cfg.get("tools", "short_name") == "a.s.t"
