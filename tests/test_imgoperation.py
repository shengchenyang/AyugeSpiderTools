from pathlib import Path

from ayugespidertools.imgoperation import Picture
from tests import tests_dir


def test_identify_gap():
    # 参数为图片全路径的情况
    gap_distance = Picture.identify_gap(
        f"{tests_dir}/docs/image/2.jpg", f"{tests_dir}/docs/image/1.png"
    )
    print("滑块验证码的缺口距离1为：", gap_distance)
    assert gap_distance in list(range(205, 218))

    # 参数为图片 bytes 的情况
    target_bytes = Path(tests_dir, "docs/image/1.png").read_bytes()
    template_bytes = Path(tests_dir, "docs/image/2.jpg").read_bytes()
    gap_distance = Picture.identify_gap(
        template_bytes, target_bytes, f"{tests_dir}/docs/image/33.png"
    )
    print("滑块验证码的缺口距离2为：", gap_distance)
    assert gap_distance in list(range(205, 218))


def test_get_data_urls_by_img():
    """根据图片参数生成 Data URLs 格式数据"""
    # 参数为图片全路径时
    data_urls1 = Picture.get_data_urls_by_img(
        mediatype="png", data=f"{tests_dir}/docs/image/1.png"
    )
    print("data_urls1:", data_urls1)

    # 参数为图片 bytes
    img_bytes = Path(tests_dir, "docs/image/1.png").read_bytes()
    data_urls2 = Picture.get_data_urls_by_img(mediatype="png", data=img_bytes)
    print("data_urls2:", data_urls2)
    assert data_urls1 is not None, data_urls2 is not None
