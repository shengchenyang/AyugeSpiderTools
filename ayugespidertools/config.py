import configparser
from importlib import import_module
from pathlib import Path

from loguru import logger
from scrapy.utils.conf import get_config

__all__ = [
    "NormalConfig",
    "logger",
    "get_cfg",
]


class NormalConfig:
    """用于存放此项目的通用配置"""

    CONFIG_DIR = Path(__file__).parent
    ROOT_DIR = CONFIG_DIR.parent
    COMMON_DIR = CONFIG_DIR / "common"
    VIT_DIR = CONFIG_DIR / "VIT"
    DATA_DIR = CONFIG_DIR / "data"


def get_cfg() -> "configparser.ConfigParser":
    _cfg = get_config(use_closest=True)
    settings_default = _cfg.get("settings", "default")
    module = import_module(settings_default)
    vit_dir = getattr(module, "VIT_DIR")
    cfg = configparser.ConfigParser()
    cfg.read(f"{vit_dir}/.conf", encoding="utf-8")
    return cfg
