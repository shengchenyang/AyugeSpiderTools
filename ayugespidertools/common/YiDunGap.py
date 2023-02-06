import itertools

import cv2

from ayugespidertools.common.MultiPlexing import ReuseOperation

__all__ = [
    "YiDunGetGap",
]


class YiDunGetGap(object):
    """
    易盾获取滑块缺口距离的相关方法，也可能适配于其它平台
    """

    @classmethod
    def clear_white(cls, img):
        """
        清除图片的空白区域，这里主要清除滑块的空白
        Args:
            img: 待处理的图片

        Returns:
            1). 清楚图片空白区域的图片
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

    @classmethod
    def template_match(cls, tpl, target, out: str = None) -> int:
        """
        模板匹配找出滑块缺口的距离
        Args:
            tpl: 缺口图片
            target: 背景图片
            out: 展示图片的存储全路径，会将绘制的图片保存至此

        Returns:
            tl[0]: 滑块缺口的距离
        """
        th, tw = tpl.shape[:2]
        result = cv2.matchTemplate(target, tpl, cv2.TM_CCOEFF_NORMED)
        # 寻找矩阵(一维数组当作向量,用Mat定义) 中最小值和最大值的位置
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        tl = max_loc

        # 是否展示标注后的图片
        if out:
            br = (tl[0] + tw, tl[1] + th)
            # 绘制矩形边框，将匹配区域标注出来
            # target：目标图像
            # tl：矩形定点
            # br：矩形的宽高
            # (0,0,255)：矩形边框颜色
            # 1：矩形边框大小
            cv2.rectangle(target, tl, br, (0, 0, 255), 2)
            cv2.imwrite(out, target)
        return tl[0]

    @classmethod
    def image_edge_detection(cls, img):
        """
        图像边缘检测处理，识别图片边缘
        Args:
            img: 需要处理的图片，用于边缘检测使用

        Returns:
            1). 处理后的图片
        """
        return cv2.Canny(img, 100, 200)

    @classmethod
    def discern(cls, slide, bg, out: str = None):
        """
        识别滑块缺口方法
        Args:
            slide: 滑块图，可以是全路径图片，也可以是图片的 bytes 数据
            bg: 带缺口的背景图，可以是全路径图片，也可以是图片的 bytes 数据
            out: 绘制图展示的存储地址，参数格式为图片的全路径

        Returns:
            x: 滑块缺口横坐标
        """
        # 先用 opencv 读取图片数据
        slide_cv, bg_cv = ReuseOperation.read_image_data(slide, bg)

        # 清除图片的空白区域
        img1 = cls.clear_white(slide_cv)
        img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        # 图像边缘检测处理
        slide = cls.image_edge_detection(img1)
        back = cls.image_edge_detection(bg_cv)

        slide_pic = cv2.cvtColor(slide, cv2.COLOR_GRAY2RGB)
        back_pic = cv2.cvtColor(back, cv2.COLOR_GRAY2RGB)
        # 输出横坐标, 即滑块在图片上的位置
        return cls.template_match(slide_pic, back_pic, out)
