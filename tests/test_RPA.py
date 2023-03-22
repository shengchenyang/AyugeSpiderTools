import pytest

from ayugespidertools.RPA import AboutPyppeteer


@pytest.mark.skip()
def test_deal_pyppeteer_suspend():
    # 暂时不测试此功能
    AboutPyppeteer.deal_pyppeteer_suspend(fn="logs/tmall.log", line=4)
    assert True
