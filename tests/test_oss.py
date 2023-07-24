from pathlib import Path

import pytest

from ayugespidertools.oss import AliOssBase

OSS_CONFIG = {
    "access_key_id": "",
    "access_key_secret": "",
    "endpoint": "",
    "bucket": "",
    "doc": "",
}


@pytest.mark.skip()
def test_put_oss():
    ali_oss = AliOssBase(**OSS_CONFIG)
    file_bytes = Path("docs/image/1.png").read_bytes()
    put_status, file_name = ali_oss.put_oss(
        put_bytes_or_url=file_bytes, file_name="1", file_format="png"
    )

    print(put_status)
    assert put_status is True


@pytest.mark.skip()
def test_enumer_file_by_pre():
    ali_oss = AliOssBase(**OSS_CONFIG)
    res = ali_oss.enumer_file_by_pre(prefix="Video_Dir")
    print(res)
    res = ali_oss.enumer_file_by_pre(prefix="Video_Dir", count_by_type="mp3")
    print(res)
    res = ali_oss.enumer_file_by_pre(prefix="Video_Dir", count_by_type=["mp3", "mp4"])
    print(res)
    assert True
