from ayugespidertools import __version__
from ayugespidertools.config import NormalConfig


def test_version():
    assert __version__ == NormalConfig.version
