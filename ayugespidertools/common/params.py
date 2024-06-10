import platform

__all__ = [
    "Param",
]


class Param:
    """用于存储项目中需要的参数变量设置"""

    retry_num = 3
    retry_time_min = 200
    retry_time_max = 1000

    aiohttp_retry_times_default = 3

    # 部署运行的平台为 win 或 linux
    IS_WINDOWS = platform.system().lower() == "windows"
    IS_LINUX = platform.system().lower() == "linux"

    # 动态隧道代理配置示例
    dynamic_proxy_conf_example = {
        "proxy": "动态隧道代理地址：***.***.com:*****",
        "username": "隧道代理用户名",
        "password": "对应用户的密码",
    }
    # 独享代理配置示例
    exclusive_proxy_conf_example = {
        "proxy": "独享代理地址：'http://***.com/api/***&num=100&format=json'",
        "username": "独享代理用户名",
        "password": "对应用户的密码",
        "index": "需要返回的独享代理的索引",
    }

    # aiohttp 配置示例
    aiohttp_conf_example = {
        "timeout": 5,
        "proxy": "127.0.0.1:80",
        "sleep": 1,
        "retry_times": 3,
    }

    charset_collate_map = {
        # utf8mb4_unicode_ci 也是经常使用的
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
