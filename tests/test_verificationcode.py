from pathlib import Path

from ayugespidertools import verificationcode
from ayugespidertools.extras.cvnpil import CvnpilKit
from tests import tests_dir


def test_match_img_get_distance():
    _left_offset = 195
    _right_offset = 210
    gap_distance = CvnpilKit.match_img_get_distance(
        f"{tests_dir}/docs/image/new_target.jpg",
        f"{tests_dir}/docs/image/new_template.png",
    )
    assert _left_offset <= gap_distance <= _right_offset

    target_bytes = Path(tests_dir, "docs/image/new_target.jpg").read_bytes()
    template_bytes = Path(tests_dir, "docs/image/new_template.png").read_bytes()
    gap_distance = CvnpilKit.match_img_get_distance(target_bytes, template_bytes)
    assert _left_offset <= gap_distance <= _right_offset


def test_get_selenium_tracks():
    tracks = verificationcode.get_selenium_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_yidun_tracks():
    tracks = verificationcode.get_yidun_tracks(distance=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_normal_track():
    tracks = CvnpilKit.get_normal_track(space=120)
    print("生成的轨迹为：", tracks)
    assert tracks


def test_get_yidun_gap():
    _left_offset = 212.5
    _right_offset = 217.5
    # 参数为图片全路径的情况
    gap_distance = verificationcode.get_yidun_gap(
        f"{tests_dir}/docs/image/1.png",
        f"{tests_dir}/docs/image/2.jpg",
        f"{tests_dir}/docs/image/3.png",
    )
    assert _left_offset <= gap_distance <= _right_offset

    # 参数为图片 bytes 的情况
    target_bytes = Path(tests_dir, "docs/image/1.png").read_bytes()
    template_bytes = Path(tests_dir, "docs/image/2.jpg").read_bytes()
    gap_distance = verificationcode.get_yidun_gap(
        target_bytes, template_bytes, f"{tests_dir}/docs/image/33.png"
    )
    assert _left_offset <= gap_distance <= _right_offset
