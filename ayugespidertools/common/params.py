import platform

__all__ = [
    "Param",
]


class Param:
    """Project constants"""

    retry_num = 3
    retry_time_min = 200
    retry_time_max = 1000
    aiohttp_retry_times_default = 3

    IS_WINDOWS = platform.system().lower() == "windows"
    IS_LINUX = platform.system().lower() == "linux"

    aiohttp_conf_example = {
        "timeout": 5,
        "proxy": "127.0.0.1:80",
        "sleep": 1,
        "retry_times": 3,
    }

    charset_collate_map = {
        # utf8mb4_unicode_ci is also frequently used
        "utf8mb4": "utf8mb4_general_ci",
        "utf8": "utf8_general_ci",
        "gbk": "gbk_chinese_ci",
        "latin1": "latin1_swedish_ci",
        "utf16": "utf16_general_ci",
        "utf16le": "utf16le_general_ci",
        "cp1251": "cp1251_general_ci",
        "euckr": "euckr_korean_ci",
        "greek": "greek_general_ci",
    }
