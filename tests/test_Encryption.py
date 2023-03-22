from ayugespidertools.common.Encryption import EncryptOperation


def test_md5():
    md5_res = EncryptOperation.md5("123456")
    assert md5_res == "e10adc3949ba59abbe56e057f20f883e"


def test_base64_encode():
    base64_encode_str_res = EncryptOperation.base64_encode(encode_data="123456")
    base64_encode_url_res = EncryptOperation.base64_encode(
        encode_data="https://www.demo.com/", url_safe=True
    )
    assert all(
        [
            base64_encode_str_res == "MTIzNDU2",
            base64_encode_url_res == "aHR0cHM6Ly93d3cuZGVtby5jb20v",
        ]
    )


def test_base64_decode():
    base64_decode_res = EncryptOperation.base64_decode(
        decode_data="MTIzNDU2",
    )

    base64_decode_url_res = EncryptOperation.base64_decode(
        decode_data="aHR0cHM6Ly93d3cuZGVtby5jb20v", url_safe=True
    )
    assert base64_decode_res == "123456", (
        base64_decode_url_res == "https://www.demo.com/"
    )


def test_mmh3_hash128_encode():
    mm3_hash128_encode_res = EncryptOperation.mm3_hash128_encode(encode_data="123456")
    assert mm3_hash128_encode_res == "e417cf050bbbd0d651a48091002531fe"


def test_rsa_encrypt():
    rsa_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCuR3+MuPOVYuAKOS6O+J/ds+JAesgyFforFupDiDBBMTItdXyMrG6gUPFxj/pT/9uQSq8Zxl7BrdiKdi0G2ppEn4Nym+VRLTv2+lNa3kvlrj25Lop7wDZkVRecK5oDvdaQHrm4KKiF7jZNbHEreWGsINLpGvzBMRNztRtOJ6+XEQIDAQAB"
    rsa_encrypted = EncryptOperation.rsa_encrypt(
        rsa_public_key=rsa_key, encode_data="123456"
    )
    assert rsa_encrypted is not None
