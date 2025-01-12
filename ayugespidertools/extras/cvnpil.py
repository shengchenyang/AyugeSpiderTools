from __future__ import annotations

import itertools
import math
import random
from typing import TYPE_CHECKING, Any

from ayugespidertools.exceptions import NotConfigured

try:
    import cv2
    import numpy as np
except ImportError:
    raise NotConfigured(
        "missing opencv-python(cv2) or numpy library, please install it. "
        "install command: pip install ayugespidertools[all]"
    )

__all__ = ["CvnpilKit", "BezierTrajectory"]

if TYPE_CHECKING:
    from cv2.typing import MatLike


class CvnpilKit:
    @staticmethod
    def get_array_dimension(array: frozenset | list | set | tuple) -> int:
        """获取 array 的维度

        Args:
            array: 数组

        Returns:
            1). 层级数
        """
        # 其实直接返回 len(array) 即可
        return len(np.array(array).shape)

    @staticmethod
    def read_image_data(img: bytes | str, flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
        """
        用 opencv 读取图片数据
        Args:
            img: 图片参数，类型需要是路径 str 或 bytes 数据
            flags: 应用颜色通道类型

        Returns:
            img_cv: opencv 读取背景图片的数据
        """
        assert type(img) in [str, bytes], "img 参数需要是路径或 bytes 数据"
        if isinstance(img, bytes):
            img_buf = np.frombuffer(img, np.uint8)
            img_cv = cv2.imdecode(img_buf, cv2.IMREAD_ANYCOLOR)
        else:
            # 读取图片，读进来直接是 BGR 格式数据格式在 0~255
            img_cv = cv2.imread(img, flags)
        return img_cv

    @staticmethod
    def clear_white(img):
        """清除图片的空白区域，这里主要清除滑块的空白

        Args:
            img: 待处理的图片

        Returns:
            1). 清除图片空白区域的图片
        """
        rows, cols, channel = img.shape
        min_x = 255
        min_y = 255
        max_x = 0
        max_y = 0
        for x, y in itertools.product(range(1, rows), range(1, cols)):
            t = set(img[x, y])
            if len(t) >= 2:
                if x <= min_x:
                    min_x = x
                elif x >= max_x:
                    max_x = x

                if y <= min_y:
                    min_y = y
                elif y >= max_y:
                    max_y = y
        return img[min_x:max_x, min_y:max_y]

    @staticmethod
    def image_edge_detection(img):
        """图像边缘检测处理，识别图片边缘

        Args:
            img: 需要处理的图片，用于边缘检测使用

        Returns:
            1). 处理后的图片
        """
        return cv2.Canny(img, 100, 200)

    @staticmethod
    def _template_match(bg: MatLike, slider: MatLike, out: str | None = None) -> int:
        """模板匹配找出滑块缺口的距离

        Args:
            bg: 背景图片
            slider: 缺口(滑块)图片
            out: 展示图片的存储全路径，会将绘制的图片保存至此

        Returns:
            tl[0]: 滑块缺口的距离
        """
        res = cv2.matchTemplate(bg, slider, cv2.TM_CCOEFF_NORMED)
        # 寻找最优匹配(一维数组当作向量,用 Mat 定义) 中最小值和最大值的位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # 左上角点的坐标
        tl = max_loc

        if out:
            # 绘制方框
            th, tw = slider.shape[:2]
            # 右下角点的坐标
            br = (tl[0] + tw, tl[1] + th)
            cv2.rectangle(bg, tl, br, (0, 0, 255), 2)
            cv2.imwrite(out, bg)
        return tl[0]

    @classmethod
    def discern_gap(
        cls, bg: str | bytes, slider: str | bytes, out: str | None = None
    ) -> int:
        """识别滑块缺口方法

        Args:
            bg: 带缺口的背景图，可以是全路径图片，也可以是图片的 bytes 数据
            slider: 滑块图，可以是全路径图片，也可以是图片的 bytes 数据
            out: 绘制图展示的存储地址，参数格式为图片的全路径

        Returns:
            1): 滑块缺口横坐标
        """
        slider_cv = CvnpilKit.read_image_data(slider)
        bg_cv = CvnpilKit.read_image_data(bg, cv2.IMREAD_GRAYSCALE)
        slider_clr = cls.clear_white(slider_cv)
        slider_clr = cv2.cvtColor(slider_clr, cv2.COLOR_RGB2GRAY)
        slider_img = cls.image_edge_detection(slider_clr)
        bg_img = cls.image_edge_detection(bg_cv)
        slider_img = cv2.cvtColor(slider_img, cv2.COLOR_GRAY2RGB)
        bg_img = cv2.cvtColor(bg_img, cv2.COLOR_GRAY2RGB)
        return cls._template_match(bg_img, slider_img, out)

    @classmethod
    def identify_gap(
        cls, bg: bytes | str, slider: bytes | str, out: str | None = None
    ) -> int:
        """通过背景图片和缺口图片识别出滑块距离

        Args:
            bg: 背景图片，可以是图片的全路径，也可以是图片的 bytes 内容
            slider: 缺口（滑块）图片，可以是图片的全路径，也可以是图片的 bytes 内容
            out: 输出图片路径，示例：doc/test.jpg；此参数如果为空，则不输出标记后的图片

        Returns:
            tl[0]: 滑块缺口距离
        """
        # 读取图片数据
        bg_cv = cls.read_image_data(bg)
        slider_cv = cls.read_image_data(slider, cv2.IMREAD_GRAYSCALE)
        # 识别图片边缘
        bg_edge = cv2.Canny(bg_cv, 100, 200)
        slider_edge = cv2.Canny(slider_cv, 100, 200)
        # 转换图片格式
        bg_img = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
        slider_img = cv2.cvtColor(slider_edge, cv2.COLOR_GRAY2RGB)
        return cls._template_match(bg_img, slider_img, out)

    @staticmethod
    def match_gap(bg: str | bytes, slider: str | bytes) -> int | None:
        """滑块坐标定位方法

        Args:
            bg: 1) 带缺口的背景图，全路径; 2) 或者是背景图的 bytes 数据
            slider: 1） 滑块图，全路径; 2）或者是滑块图的 bytes 数据

        Returns:
            loc[1][0]: 滑块位置坐标
        """
        bg_cv = CvnpilKit.read_image_data(bg, cv2.IMREAD_GRAYSCALE)
        slider_cv = CvnpilKit.read_image_data(slider, cv2.IMREAD_GRAYSCALE)

        run = 1
        # 这里的返回值根据不同版本的 open-cv 其返回结果会有不同的个数
        # w, h, z = slider_cv.shape[::-1]
        # 在背景图里面查找滑块图的位置
        res = cv2.matchTemplate(bg_cv, slider_cv, cv2.TM_CCOEFF_NORMED)
        # 使用二分法查找阈值的精确值
        lft: float = 0.0
        rgt: float = 1.0
        loc: tuple[np.ndarray[Any, np.dtype[np.signedinteger[Any]]], ...] = ()
        while run < 20:
            run += 1
            threshold = (rgt + lft) / 2
            if threshold < 0:
                # 逻辑走到这里，则说明出错了，并未找出目标位置
                return None

            # 匹配程度大于百分之 threshold 的坐标 x, y
            loc = np.where(res >= threshold)
            if len(loc[1]) > 1:
                rgt += (rgt - lft) / 2
            elif len(loc[1]) == 1:
                # 找到目标区域起点 x 坐标为：loc[1][0]
                break
            elif len(loc[1]) < 1:
                rgt -= (rgt - lft) / 2
        return loc[1][0]

    @staticmethod
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


class BezierTrajectory:
    """贝塞尔曲线轨迹生成器

    Examples:
        >>> bt = BezierTrajectory()
        >>> gen_data = bt.gen_track(start=[50, 268], end=[367, 485], num=45, order=4, mode=2)
        >>> track = gen_data["trackArray"]
    """

    def _generate_control_points(self, track: list):
        """计算贝塞尔曲线的控制点"""
        track_len = len(track)

        def calculate_bezier_point(x):
            t = (x - track[0][0]) / (track[-1][0] - track[0][0])
            y = np.array([0, 0], dtype=np.float64)
            for s in range(len(track)):
                y += track[s] * (
                    (
                        math.factorial(track_len - 1)
                        / (math.factorial(s) * math.factorial(track_len - 1 - s))
                    )
                    * math.pow(t, s)
                    * math.pow((1 - t), track_len - 1 - s)
                )
            return y[1]

        return calculate_bezier_point

    def _type(self, mode, x, length):
        numbers = []
        pin = (x[1] - x[0]) / length
        if mode == 0:
            numbers.extend(i * pin for i in range(length))
            if pin >= 0:
                numbers = numbers[::-1]
        elif mode == 1:
            for i in range(length):
                numbers.append(1 * ((i * pin) ** 2))
            numbers = numbers[::-1]
        elif mode == 2:
            for i in range(length):
                numbers.append(1 * ((i * pin - x[1]) ** 2))

        elif mode == 3:
            track = [
                np.array([0, 0]),
                np.array([(x[1] - x[0]) * 0.8, (x[1] - x[0]) * 0.6]),
                np.array([x[1] - x[0], 0]),
            ]
            fun = self._generate_control_points(track)
            numbers = [0]
            numbers.extend(fun(i * pin) + numbers[-1] for i in range(1, length))
            if pin >= 0:
                numbers = numbers[::-1]
        numbers = np.abs(np.array(numbers) - max(numbers))
        normal_numbers = (
            (numbers - numbers[numbers.argmin()])
            / (numbers[numbers.argmax()] - numbers[numbers.argmin()])
        ) * (x[1] - x[0]) + x[0]
        normal_numbers[0] = x[0]
        normal_numbers[-1] = x[1]
        return normal_numbers

    def simulation(self, start, end, order=1, deviation=0, bias=0.5):
        """模拟贝塞尔曲线的绘制过程

        Args:
            start: 开始点的坐标
            end: 结束点的坐标
            order: 几阶贝塞尔曲线，越大越复杂
            deviation: 轨迹上下波动的范围
            bias: 波动范围的分布位置

        Returns:
            1). 返回一个字典 equation 对应该曲线的方程，P 对应贝塞尔曲线的影响点
        """
        start = np.array(start)
        end = np.array(end)
        shake_num = []
        if order != 1:
            e = (1 - bias) / (order - 1)
            shake_num = [[bias + e * i, bias + e * (i + 1)] for i in range(order - 1)]

        track_lst = [start]

        t = random.choice([-1, 1])
        w = 0
        for i in shake_num:
            px1 = start[0] + (end[0] - start[0]) * (
                random.random() * (i[1] - i[0]) + (i[0])
            )
            p = np.array(
                [px1, self._generate_control_points([start, end])(px1) + t * deviation]
            )
            track_lst.append(p)
            w += 1
            if w >= 2:
                w = 0
                t = -1 * t

        track_lst.append(end)
        return {
            "equation": self._generate_control_points(track_lst),
            "P": np.array(track_lst),
        }

    def gen_track(
        self,
        start: np.ndarray | list,
        end: np.ndarray | list,
        num: int,
        order: int = 1,
        deviation: int = 0,
        bias=0.5,
        mode=0,
        shake_num=0,
        yhh=10,
    ) -> dict:
        """生成轨迹数组

        Args:
            start: 开始点的坐标
            end: 结束点的坐标
            num: 返回的数组的轨迹点的数量
            order: 几阶贝塞尔曲线，越大越复杂
            deviation: 轨迹上下波动的范围
            bias: 波动范围的分布位置
            mode: 0 表示均速滑动，1 表示先慢后快，2 表示先快后慢，3 表示先慢中间快后慢
            shake_num: 在终点来回摆动的次数
            yhh: 在终点来回摆动的范围

        Returns:
            1). 返回一个字典 trackArray 对应轨迹数组，P 对应贝塞尔曲线的影响点
        """
        s: list = []
        fun = self.simulation(start, end, order, deviation, bias)
        w = fun["P"]
        fun = fun["equation"]
        if shake_num != 0:
            track_number = round(num * 0.2 / (shake_num + 1))
            num -= track_number * (shake_num + 1)

            x_track_array = self._type(mode, [start[0], end[0]], num)
            s.extend([i, fun(i)] for i in x_track_array)
            dq = yhh / shake_num
            kg = 0
            ends = np.copy(end)
            for i in range(shake_num):
                if kg == 0:
                    d = np.array(
                        [
                            end[0] + (yhh - dq * i),
                            ((end[1] - start[1]) / (end[0] - start[0]))
                            * (end[0] + (yhh - dq * i))
                            + (
                                end[1]
                                - ((end[1] - start[1]) / (end[0] - start[0])) * end[0]
                            ),
                        ]
                    )
                    kg = 1
                else:
                    d = np.array(
                        [
                            end[0] - (yhh - dq * i),
                            ((end[1] - start[1]) / (end[0] - start[0]))
                            * (end[0] - (yhh - dq * i))
                            + (
                                end[1]
                                - ((end[1] - start[1]) / (end[0] - start[0])) * end[0]
                            ),
                        ]
                    )
                    kg = 0
                y = self.gen_track(
                    ends,
                    d,
                    track_number,
                    order=2,
                    deviation=0,
                    bias=0.5,
                    mode=0,
                    shake_num=0,
                    yhh=10,
                )
                s += list(y["trackArray"])
                ends = d
            y = self.gen_track(
                ends,
                end,
                track_number,
                order=2,
                deviation=0,
                bias=0.5,
                mode=0,
                shake_num=0,
                yhh=10,
            )
            s += list(y["trackArray"])

        else:
            x_track_array = self._type(mode, [start[0], end[0]], num)
            s.extend([i, fun(i)] for i in x_track_array)
        return {"trackArray": np.array(s), "P": w}
