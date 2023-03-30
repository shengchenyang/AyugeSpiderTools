import pytest

from ayugespidertools.commands.genspider import AyuCommand


@pytest.mark.skip()
def test_genspider():
    AyuCommand().run(["demo_one", "csdn.net"], None)
    assert True
