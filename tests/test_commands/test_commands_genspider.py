from ayugespidertools.commands.genspider import AyuCommand


def test_genspider():
    AyuCommand().run(["demo_one", "csdn.net"], None)
    assert True
