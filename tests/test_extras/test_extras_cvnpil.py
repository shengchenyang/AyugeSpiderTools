from pathlib import Path

from ayugespidertools.common.utils import ToolsForAyu
from ayugespidertools.extras.cvnpil import CvnpilKit
from tests import tests_dir


def test_get_array_dimension():
    # 二维数组
    a = [[1, 2], [3, 4]]
    # 一维数组
    b = [1, 2, 3]
    # 三维数组
    c = [[[1], [2]], [[3], [4]]]
    len1 = CvnpilKit.get_array_dimension(array=a)
    len2 = CvnpilKit.get_array_dimension(array=b)
    len3 = CvnpilKit.get_array_dimension(array=c)
    print("res len1:", len1)
    print("res len2:", len2)
    print("res len3:", len3)
    assert all([len1 == 2, len2 == 1, len3 == 3])


def test_identify_gap():
    # 参数为图片全路径的情况
    gap_distance = CvnpilKit.identify_gap(
        f"{tests_dir}/docs/image/2.jpg", f"{tests_dir}/docs/image/1.png"
    )
    print("滑块验证码的缺口距离1为：", gap_distance)
    assert gap_distance in list(range(205, 218))

    # 参数为图片 bytes 的情况
    target_bytes = Path(tests_dir, "docs/image/1.png").read_bytes()
    template_bytes = Path(tests_dir, "docs/image/2.jpg").read_bytes()
    gap_distance = CvnpilKit.identify_gap(
        template_bytes, target_bytes, f"{tests_dir}/docs/image/33.png"
    )
    print("滑块验证码的缺口距离2为：", gap_distance)
    assert gap_distance in list(range(205, 218))


def test_get_data_urls_by_img():
    """根据图片参数生成 Data URLs 格式数据"""
    # 参数为图片全路径时
    data_urls1 = ToolsForAyu.get_data_urls_by_img(
        mediatype="png", data=f"{tests_dir}/docs/image/1.png"
    )
    print("data_urls1:", data_urls1)

    # 参数为图片 bytes
    img_bytes = Path(tests_dir, "docs/image/1.png").read_bytes()
    data_urls2 = ToolsForAyu.get_data_urls_by_img(mediatype="png", data=img_bytes)
    print("data_urls2:", data_urls2)
    assert data_urls1 is not None, data_urls2 is not None
