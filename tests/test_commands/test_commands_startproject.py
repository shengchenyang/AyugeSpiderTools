from ayugespidertools.commands.startproject import AyuCommand


def test_startproject():
    AyuCommand().run(["startproject", "DemoSpider"], None)
    assert True
