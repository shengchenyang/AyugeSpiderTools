from pathlib import Path

from ayugespidertools import verificationcode
from tests import tests_dir


def test_match_img_get_distance():
    distance_res = verificationcode.match_img_get_distance(
        f"{tests_dir}/docs/image/new_target.jpg",
        f"{tests_dir}/docs/image/new_template.png",
    )
    print(f"滑块缺口位置1: {distance_res}")
    target_bytes = Path(tests_dir, "docs/image/new_target.jpg").read_bytes()
    template_bytes = Path(tests_dir, "docs/image/new_template.png").read_bytes()
    distance_res = verificationcode.match_img_get_distance(target_bytes, template_bytes)
    print(f"滑块缺口位置2： {distance_res}")
    assert distance_res in list(range(195, 210))


def test_get_selenium_tracks():
    tracks = verificationcode.get_selenium_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_yidun_tracks():
    tracks = verificationcode.get_yidun_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_normal_track():
    tracks = verificationcode.get_normal_track(space=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_yidun_gap():
    # 参数为图片全路径的情况
    tracks = verificationcode.get_yidun_gap(
        f"{tests_dir}/docs/image/1.png",
        f"{tests_dir}/docs/image/2.jpg",
        f"{tests_dir}/docs/image/3.png",
    )
    print("滑块缺口距离 1 为：", tracks)
    assert tracks == 214

    # 参数为图片 bytes 的情况
    target_bytes = Path(tests_dir, "docs/image/1.png").read_bytes()
    template_bytes = Path(tests_dir, "docs/image/2.jpg").read_bytes()
    tracks = verificationcode.get_yidun_gap(
        target_bytes, template_bytes, f"{tests_dir}/docs/image/33.png"
    )
    print("滑块缺口距离 2 为：", tracks)
    assert tracks
