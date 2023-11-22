import base64
import xml.etree.ElementTree as ET

try:
    import hcl2
    import mmh3
    import yaml
    from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcsl_v1_5
    from Crypto.PublicKey import RSA
except ImportError:
    # pip install ayugespidertools[all]
    pass

__all__ = ["EncryptMixin", "AppConfManageMixin"]


class EncryptMixin:
    @staticmethod
    def mm3_hash128_encode(encode_data: str) -> str:
        """MurmurHash3 非加密哈希之 hash128

        Args:
            encode_data: 需要 mmh3 hash128 的参数

        Returns:
            1). mmh3 hash128 后的结果
        """
        o = mmh3.hash128(encode_data)
        hash128_encoded = hex(((o & 0xFFFFFFFFFFFFFFFF) << 64) + (o >> 64))
        return hash128_encoded[2:]

    @staticmethod
    def rsa_encrypt(rsa_public_key: str, encode_data: str) -> str:
        """rsa encode example

        Args:
            rsa_public_key: rsa publickey
            encode_data: rsa encode data

        Returns:
            1). rsa encrypted result
        """
        public_key = """-----BEGIN PUBLIC KEY-----
            {key}
            -----END PUBLIC KEY-----""".format(
            key=rsa_public_key
        )
        a = bytes(encode_data, encoding="utf8")
        rsa_key = RSA.importKey(public_key)
        cipher = Cipher_pkcsl_v1_5.new(rsa_key)
        return str(base64.b64encode(cipher.encrypt(a)), encoding="utf-8")


class AppConfManageMixin:
    @staticmethod
    def hcl_parser(data: str) -> dict:
        return hcl2.loads(data)

    @staticmethod
    def yaml_parser(data: str) -> dict:
        return yaml.safe_load(data)

    @staticmethod
    def xml_parser(data: str) -> dict:
        root = ET.fromstring(data)
        conf_data = {}
        for child in root:
            conf_data[child.tag] = {}
            for sub_child in child:
                conf_data[child.tag][sub_child.tag] = sub_child.text
        return conf_data
