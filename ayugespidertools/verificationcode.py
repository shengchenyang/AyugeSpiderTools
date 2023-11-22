import random
from typing import Optional, Union

from ayugespidertools.extras.cvnpil import CvnpilKit

__all__ = [
    "get_selenium_tracks",
    "get_yidun_tracks",
    "get_yidun_gap",
]


def get_selenium_tracks(distance):
    """最简陋的根据缺口距离获取轨迹的方法，以供 selenium 使用

    Args:
        distance: 滑块缺口的距离

    Returns:
        tracks_dict:
            forward_tracks: 往右划的轨迹数组
            back_tracks: 回退（往左划）的轨迹数组
    """
    distance += 20
    v = 0
    t = 0.2
    forward_tracks = []
    current = 0
    mid = distance * 3 / 5
    while current < distance:
        a = 2 if current < mid else -3
        s = v * t + 0.5 * a * (t**2)
        v = v + a * t
        current += s
        forward_tracks.append(round(s))

    back_tracks = [-3, -3, -2, -2, -2, -2, -2, -1, -1, -1]
    return {"forward_tracks": forward_tracks, "back_tracks": back_tracks}


def get_yidun_tracks(distance):
    """轨迹生成方法

    Args:
        distance: 滑块缺口的距离

    Returns:
        xyt: 轨迹数组
    """
    t_list = [random.randint(50, 160)]
    x_list = [random.randint(5, 11)]
    y_list = []
    # 生成x坐标轨迹, 生成t坐标轨迹
    for j in range(1, distance):
        x_list.append(x_list[j - 1] + random.randint(2, 4))
        if x_list[j] > distance:
            break

    diff = x_list[-1] - distance
    for j in range(diff):
        x_list.append(x_list[-1] + random.randint(-2, -1))
        if x_list[-1] <= distance:
            x_list[-1] = distance
            break

    length = len(x_list)
    # 生成y坐标轨迹
    for i in range(1, length + 1):
        if i < int(length * 0.4):
            y_list.append(0)
        elif i < int(length * 0.65):
            y_list.append(-1)
        elif i < int(length * 0.77):
            y_list.append(-2)
        elif i < int(length * 0.95):
            y_list.append(-3)
        else:
            y_list.append(-4)
        t_list.append(t_list[i - 1] + random.randint(20, 80))

    # 生成t的坐标
    xyt = list(zip(x_list, y_list, t_list))
    for j in range(length):
        xyt[j] = list(xyt[j])
    return xyt


def get_yidun_gap(
    slide_img_path: Union[str, bytes],
    bg_img_path: Union[str, bytes],
    out_img_path: Optional[str] = None,
) -> int:
    """获取滑块缺口距离

    Args:
        slide_img_path: 滑块的图片
        bg_img_path: 带缺口的背景图片
        out_img_path: 输出图片

    Returns:
        1). 滑块缺口距离
    """
    return CvnpilKit.discern(slide_img_path, bg_img_path, out_img_path)
