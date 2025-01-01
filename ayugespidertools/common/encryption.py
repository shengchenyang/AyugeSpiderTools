from __future__ import annotations

import base64
import hashlib
import re

from ayugespidertools.extras.ext import EncryptMixin

__all__ = [
    "Encrypt",
]


class Encrypt(EncryptMixin):
    """普通加密方法"""

    @staticmethod
    def md5(encrypt_data: str) -> str:
        """md5 处理方法

        Args:
            encrypt_data: 需要 md5 处理的参数

        Returns:
            1). md5 处理后的参数
        """
        hl = hashlib.md5()
        hl.update(encrypt_data.encode(encoding="utf-8"))
        return hl.hexdigest()

    @staticmethod
    def base64_encode(encode_data: bytes | str, url_safe: bool = False) -> str:
        """base64 编码

        Args:
            encode_data: 需要 base64 编码的参数
            url_safe: 标准的 Base64 编码后可能出现字符 + 和 /，在 url 中就不能直接作为参数。是否要处理此情况

        Returns:
            1). base64 编码后的结果
        """
        if not isinstance(encode_data, bytes):
            encode_data = bytes(encode_data, encoding="utf-8")
        if url_safe:
            return str(base64.urlsafe_b64encode(encode_data), encoding="utf-8")
        return str(base64.b64encode(encode_data), encoding="utf-8")

    @staticmethod
    def base64_decode(decode_data: str, url_safe: bool = False) -> str:
        """base64 解码

        Args:
            decode_data: 需要 base64 解码的参数
            url_safe: 标准的 Base64 编码后可能出现字符 + 和 /，在 url 中就不能直接作为参数。是否要处理此情况

        Returns:
            1). base64 解码后的结果
        """
        if url_safe:
            return str(base64.urlsafe_b64decode(decode_data), encoding="utf-8")
        return str(base64.b64decode(decode_data), encoding="utf-8")

    @staticmethod
    def uni_to_chr(uni: str) -> str:
        """将 Unicode 码位表示的字符串转换正常的字符，用于获取字体映射时使用

        Args:
            uni: 需要转换的 unicode 字符串，
                如：006A，但它可能是非标准的，可能需要去掉前面的 0x 或 uni。

        Returns:
            1). 转换后的字符
        """
        _uni = re.sub(r"^(0x|U\+|uni)", "", uni)
        unicode_value = int(_uni, 16)
        return chr(unicode_value)
