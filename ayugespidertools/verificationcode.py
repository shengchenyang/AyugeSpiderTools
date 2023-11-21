import math
import random
from typing import Optional, Union

import cv2
import numpy as np

from ayugespidertools.common.yidungap import YiDunGetGap

__all__ = [
    "match_img_get_distance",
    "get_selenium_tracks",
    "get_yidun_tracks",
    "get_yidun_gap",
    "get_normal_track",
]


def match_img_get_distance(target, template):
    """滑块坐标定位方法

    Args:
        target: 1) 带缺口的背景图，全路径; 2) 或者是背景图的 bytes 数据
        template: 1） 滑块图，全路径; 2）或者是滑块图的 bytes 数据

    Returns:
        loc[1][0]: 滑块位置坐标
    """
    # 先判断传入的参数是 str 图片的全路径信息还是 bytes 类型的图片信息
    if any([not isinstance(target, str), isinstance(target, bytes)]):
        target_buf = np.frombuffer(target, np.uint8)
        template_buf = np.frombuffer(template, np.uint8)

        target_cv = cv2.imdecode(target_buf, cv2.IMREAD_ANYCOLOR)
        template_cv = cv2.imdecode(template_buf, cv2.IMREAD_ANYCOLOR)

    else:
        # 读取图片，读进来直接是 BGR 格式数据格式在 0~255
        target_cv = cv2.imread(target)
        # 0 表示采用黑白的方式读取图片
        template_cv = cv2.imread(template, 0)

        # cv2.cvtColor(p1,p2) 是颜色空间转换函数，p1是需要转换的图片，p2是转换成何种格式。
        # cv2.COLOR_BGR2GRAY 将BGR格式转换成灰度图片，发现转换后并不是通常意义上的黑白图片。
        # 灰度图片并不是指常规意义上的黑白图片，只用看是不是无符号八位整型（unit8）,单通道即可判断。
        target_cv = cv2.cvtColor(target_cv, cv2.COLOR_BGR2GRAY)

    run = 1
    # 这里的返回值根据不同版本的 open-cv 其返回结果会有不同的个数
    # w, h, z = template_cv.shape[::-1]
    # 在背景图里面查找滑块图的位置
    res = cv2.matchTemplate(target_cv, template_cv, cv2.TM_CCOEFF_NORMED)
    # 使用二分法查找阈值的精确值
    L = 0
    R = 1
    loc = None
    while run < 20:
        run += 1
        threshold = (R + L) / 2
        if threshold < 0:
            # 逻辑走到这里，则说明出错了，并未找出目标位置
            return None

        # 匹配程度大于百分之 threshold 的坐标 x, y
        loc = np.where(res >= threshold)
        if len(loc[1]) > 1:
            L += (R - L) / 2
        elif len(loc[1]) == 1:
            # 找到目标区域起点x坐标为：loc[1][0]
            break
        elif len(loc[1]) < 1:
            R -= (R - L) / 2

    # 返回 x 坐标
    return loc[1][0]


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
    return YiDunGetGap.discern(slide_img_path, bg_img_path, out_img_path)


def get_normal_track(space):
    """通用的根据滑块距离获取轨迹数组方法

    Args:
        space: 滑块缺口距离

    Returns:
        tracks_list: 生成的轨迹数组
    """
    x = [0, 0]
    y = [0, 0, 0]
    z = [0]
    # x
    count = np.linspace(-math.pi / 2, math.pi / 2, random.randrange(20, 30))
    func = list(map(math.sin, count))
    nx = [i + 1 for i in func]
    add = random.randrange(10, 15)
    sadd = space + add
    x.extend(list(map(lambda x: x * (sadd / 2), nx)))
    # x.extend(np.linspace(sadd, space, 4 if add > 12 else 3))
    x.extend(np.linspace(sadd, space, 3 if add > 12 else 2))
    x = [math.floor(i) for i in x]
    # y
    for i in range(len(x) - 2):
        if y[-1] < 30:
            y.append(y[-1] + random.choice([0, 0, 1, 1, 2, 2, 1, 2, 0, 0, 3, 3]))
        else:
            y.append(
                y[-1] + random.choice([0, 0, -1, -1, -2, -2, -1, -2, 0, 0, -3, -3])
            )
    # z
    for i in range(len(x) - 1):
        # z.append((z[-1] // 100 * 100) + 100 + random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2]))
        z.append(
            (z[-1] // 100 * 100)
            + 100
            + random.choice([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3])
        )

    tracks_list = list(map(list, zip(x, y, z)))
    tracks_list = [x for x in tracks_list if x[0] > 0]
    return tracks_list
