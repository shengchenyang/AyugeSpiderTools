from __future__ import absolute_import
import sys
import pkgutil
import warnings
from twisted import version as _txv


__all__ = [
    '__version__', 'version_info', 'twisted_version',
]


# AyugeSpiderTools and Twisted versions
__version__ = (pkgutil.get_data(__package__, "VERSION") or b"").decode("ascii").strip()
version_info = tuple(int(v) if v.isdigit() else v for v in __version__.split('.'))
twisted_version = (_txv.major, _txv.minor, _txv.micro)


# Check minimum required Python version
if sys.version_info < (3, 7):
    print(f"AyugeSpiderTools {__version__} requires Python 3.8+")
    sys.exit(1)


del pkgutil
del sys
del warnings
