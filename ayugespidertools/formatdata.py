from __future__ import annotations

import re
from urllib.parse import urljoin

from w3lib.html import remove_tags, replace_entities

__all__ = [
    "DataHandle",
]


class DataHandle:
    @staticmethod
    def get_full_url(domain_name: str, deal_url: str) -> str:
        return urljoin(domain_name, deal_url)

    @staticmethod
    def click_point_deal(decimal: float, decimal_places: int = 2) -> float:
        """Round a number to the specified number of decimal places."""
        decimal_deal = f"%.{decimal_places}f"
        return float(decimal_deal % decimal)

    @staticmethod
    def judge_include_letter(local_time: str) -> bool:
        pattern = re.compile(r"""[a-zA-Z]""")
        return bool(pattern.findall(local_time.lower()))

    @staticmethod
    def remove_all_tags(func):
        def inner(*args, **kwargs):
            func_res = func(*args, **kwargs)
            return remove_tags(func_res)

        return inner

    @staticmethod
    def normal_display(func):
        def inner(*args, **kwargs):
            func_res = func(*args, **kwargs)
            return replace_entities(func_res)

        return inner

    @staticmethod
    def simple_deal_for_extract(func):
        def inner(*args, **kwargs):
            func_res = func(*args, **kwargs)
            if type(func_res) in [str, int, float, bool]:
                return str(func_res).strip()
            return func_res

        return inner
