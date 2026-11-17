from __future__ import annotations

import base64
import hashlib
import re

from ayugespidertools.extras.ext import EncryptMixin

__all__ = [
    "Encrypt",
]


class Encrypt(EncryptMixin):
    @staticmethod
    def md5(encrypt_data: str) -> str:
        hl = hashlib.md5()  # noqa: S324
        hl.update(encrypt_data.encode(encoding="utf-8"))
        return hl.hexdigest()

    @staticmethod
    def base64_encode(encode_data: bytes | str, url_safe: bool = False) -> str:
        """Base64 encode.

        Args:
            encode_data: The data to be Base64-encoded.
            url_safe: Whether to use URL-safe Base64 encoding. Standard Base64
                may contain the characters '+' and '/', which cannot be used
                directly in URL parameters.

        Returns:
            The Base64-encoded result.
        """
        if not isinstance(encode_data, bytes):
            encode_data = bytes(encode_data, encoding="utf-8")
        if url_safe:
            return str(base64.urlsafe_b64encode(encode_data), encoding="utf-8")
        return str(base64.b64encode(encode_data), encoding="utf-8")

    @staticmethod
    def base64_decode(decode_data: str, url_safe: bool = False) -> str:
        """Base64 decode.

        Args:
            decode_data: The data to be Base64-decoded.
            url_safe: Whether to use URL-safe Base64 decoding. Standard Base64
                may contain the characters '+' and '/', which cannot be used
                directly in URL parameters.

        Returns:
            The decoded result as a string.
        """
        if url_safe:
            return str(base64.urlsafe_b64decode(decode_data), encoding="utf-8")
        return str(base64.b64decode(decode_data), encoding="utf-8")

    @staticmethod
    def uni_to_chr(uni: str) -> str:
        """Convert a Unicode code point string into its corresponding character.

        Used for retrieving font mappings.

        Args:
            uni: The Unicode code point to convert, such as "006A".
                Non-standard prefixes such as "0x" or "uni" may need to be removed.

        Returns:
            The converted character.
        """
        _uni = re.sub(r"^(0x|U\+|uni)", "", uni)
        unicode_value = int(_uni, 16)
        return chr(unicode_value)
