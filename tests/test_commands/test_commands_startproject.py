import pytest

from ayugespidertools.commands.startproject import AyuCommand


@pytest.mark.skip()
def test_startproject():
    AyuCommand().run(["startproject", "DemoSpider"], None)
    assert True
