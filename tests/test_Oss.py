from ayugespidertools.Oss import AliOssBase

OSS_CONFIG = {
    "OssAccessKeyId": "",
    "OssAccessKeySecret": "",
    "Endpoint": "",
    "examplebucket": "",
    "operateDoc": "",
}

ali_oss = AliOssBase(**OSS_CONFIG)


def test_put_oss():
    # 连接 ali oss
    with open("docs/image/1.png", "rb") as f:
        file_bytes = f.read()

    put_status, file_name = ali_oss.put_oss(
        put_bytes_or_url=file_bytes, file_name="1", file_format="png"
    )

    print(put_status)
    assert put_status is True


def test_enumer_file_by_pre():
    res = ali_oss.enumer_file_by_pre(prefix="Video_Dir")
    print(res)
    res = ali_oss.enumer_file_by_pre(prefix="Video_Dir", count_by_type="mp3")
    print(res)
    res = ali_oss.enumer_file_by_pre(prefix="Video_Dir", count_by_type=["mp3", "mp4"])
    print(res)
    assert True
