from pathlib import Path

from loguru import logger

__all__ = [
    "NormalConfig",
    "logger",
]


class NormalConfig:
    """用于存放此项目的通用配置"""

    # 项目根目录及其它所需目录
    CONFIG_DIR = Path(__file__).parent
    ROOT_DIR = CONFIG_DIR.parent
    COMMON_DIR = CONFIG_DIR / "common"
    VIT_DIR = CONFIG_DIR / "VIT"
