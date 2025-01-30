import configparser
import importlib
from importlib import import_module
from pathlib import Path

from loguru import logger
from scrapy.utils.conf import get_config

from ayugespidertools.exceptions import NotConfigured

__all__ = [
    "NormalConfig",
    "logger",
    "get_cfg",
    "setup_lazy_import",
]


class NormalConfig:
    """store the general configuration"""

    CONFIG_DIR = Path(__file__).parent
    ROOT_DIR = CONFIG_DIR.parent
    COMMON_DIR = CONFIG_DIR / "common"
    VIT_DIR = CONFIG_DIR / "VIT"
    DATA_DIR = CONFIG_DIR / "data"


def get_cfg() -> configparser.ConfigParser:
    _cfg = get_config(use_closest=True)
    settings_default = _cfg.get("settings", "default")
    module = import_module(settings_default)
    vit_dir = getattr(module, "VIT_DIR")
    cfg = configparser.ConfigParser()
    cfg.read(f"{vit_dir}/.conf", encoding="utf-8")
    return cfg


def setup_lazy_import(modules_map, base_package, globals_dict):
    """lazy import for middlewares and pipelines"""
    class_map = {}
    for submodule, classes in modules_map.items():
        for cls in classes:
            class_map[cls] = submodule

    _all = list(class_map.keys())
    globals_dict["__all__"] = _all

    def __getattr__(name):
        if name not in class_map:
            if name in _all:
                raise NotConfigured(
                    f"Class '{name}' is listed in __all__ but not configured in class_map. "
                    "Please check your modules_map."
                )
            raise NotConfigured(
                f"module {globals_dict['__name__']!r} has no attribute {name!r}"
            )

        submodule = class_map[name]
        module_path = f"{base_package}.{submodule}"
        module = importlib.import_module(module_path)
        _cls = getattr(module, name)
        globals_dict[name] = _cls
        return _cls

    def __dir__():
        return _all

    globals_dict["__getattr__"] = __getattr__
    globals_dict["__dir__"] = __dir__
