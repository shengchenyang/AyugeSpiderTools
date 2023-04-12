from typing import Optional, Union

import cv2
from PIL import Image

from ayugespidertools.common.Encryption import EncryptOperation
from ayugespidertools.common.MultiPlexing import ReuseOperation

__all__ = [
    "Picture",
]


class Picture(object):
    """
    对验证码图片的一些操作
    """

    @classmethod
    def convert_index_to_offset(cls, index):
        """
        获取每张小图的偏移量
        Args:
            index: 当前小块图片

        Returns:
            当前小图在空白图片的坐标
        """

        # 代码注释
        """
        # 图片大小为：334 159， 22 为 334 / 15 得到，58 是 159 /
        if index < 15:  # 完整的验证码图片是由30个小图片组合而成，共2行15列
            return (index * 22, 0)
        else:
            i = index - 15
            return (i * 22, 58)  # 每张小图的大小为22*58
        """
        # 完整的验证码图片是由 40 个小图片组合而成，共 2 行 15 列
        if index < 20:
            return index * 13, 0
        else:
            i = index - 20
            # 每张小图的大小为 22 * 58
            return i * 13, 58

    @classmethod
    def convert_css_to_offset(cls, off):
        """
        获取每张小图的坐标，供抠图时使用
        Args:
            off: 根据 css backgound-position 中获取的每张小图的坐标

        Returns:
            (int(off[0]), int(off[1]), int(off[0]) + 22, int(off[1]) + 58): 每张小图对应的坐标
        """
        # (left, upper)o ----- o
        #              |       |
        #              o ----- o(right, lower)
        return int(off[0]), int(off[1]), int(off[0]) + 22, int(off[1]) + 58

    @classmethod
    def recombine_captcha(cls, offset_list: list, img_path: str):
        """
        图片重组: 完美世界网站的图片重组方法
        Args:
            offset_list: 坐标列表
            img_path: 图片保存路径

        Returns:
            None
        """
        # 新建空白图片
        captcha = Image.new("RGB", (13 * 20, 60 * 2 - 4))
        # 实例化原始图片Image对象
        img = Image.open(f"{img_path}/captcha.png")

        # 切割滑块验证码图片，将背景图和滑块图分开
        # (left, upper, right, lower)
        captcha_de = img.crop((0, 0, 260, 120 - 4))
        captcha_de = captcha_de.convert("RGBA")
        captcha_de.save(f"{img_path}/captcha.png")

        for i, off in enumerate(offset_list):
            # 根据css background-position获取每张小图的坐标
            box = Picture.convert_css_to_offset(off)
            # 抠图
            regoin = img.crop(box)
            # 获取当前小图在空白图片的坐标
            offset = Picture.convert_index_to_offset(i)
            # 根据当前坐标将小图粘贴到空白图片
            captcha.paste(regoin, offset)
        captcha.save(f"{img_path}/regoin.jpg")

    @classmethod
    def reset_pic(cls, slide_data):
        """
        完美世界滑块验证码重组方法，具体位置根据 background-position 搜索定位
        Args:
            slide_data: 完美滑块重组所需的数组

        Returns:
            true_pic_list: 真实图片的顺序坐标
        """
        c = 260
        # d = 120
        _l = 20
        # s = 9
        # a = 61
        true_pic_list = []
        for curr_data in slide_data:
            curr_position_list = []
            if curr_data < _l:
                curr_position_list.extend((int(c / _l * curr_data), 0))
            else:
                curr_position_list.extend((int(c / _l * (curr_data % _l)), 60))
            true_pic_list.append(curr_position_list)
        return true_pic_list

    @classmethod
    def find_pic(cls, target, template):
        """
        找出图像中最佳匹配位置
        Args:
            target: 目标（背景图）
            template: 模板（需要找到的图）

        Returns:
            value[2:][0][0]: 返回最佳匹配及对应的坐标
            value[2:][1][0]: 返回最差匹配及对应的坐标
        """
        target_rgb = cv2.imread(target)
        target_gray = cv2.cvtColor(target_rgb, cv2.COLOR_BGR2GRAY)
        template_rgb = cv2.imread(template, 0)
        res = cv2.matchTemplate(target_gray, template_rgb, cv2.TM_CCOEFF_NORMED)
        value = cv2.minMaxLoc(res)
        return value[2:][0][0], value[2:][1][0]

    @classmethod
    def identify_gap(
        cls, bg: Union[bytes, str], tp: Union[bytes, str], out: Optional[str] = None
    ) -> int:
        """
        通过背景图片和缺口图片识别出滑块距离
        Args:
            bg: 背景图片，可以是图片的全路径，也可以是图片的 bytes 内容
            tp: 缺口（滑块）图片，可以是图片的全路径，也可以是图片的 bytes 内容
            out: 输出图片路径，示例：doc/test.jpg；此参数如果为空，则不输出标记后的图片

        Returns:
            tl[0]: 滑块缺口距离
        """
        # 先读使用 opencv 读取图片数据
        bg_cv, tp_cv = ReuseOperation.read_image_data(bg, tp)

        # 识别图片边缘
        bg_edge = cv2.Canny(bg_cv, 100, 200)
        tp_edge = cv2.Canny(tp_cv, 100, 200)

        # 转换图片格式
        bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
        tp_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)

        # 缺口匹配
        res = cv2.matchTemplate(bg_pic, tp_pic, cv2.TM_CCOEFF_NORMED)
        # 寻找最优匹配
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # 左上角点的坐标
        tl = max_loc

        # 是否要输出绘制图像
        if out:
            # 绘制方框
            th, tw = tp_pic.shape[:2]
            # 右下角点的坐标
            br = (tl[0] + tw, tl[1] + th)
            # 绘制矩形
            cv2.rectangle(bg_cv, tl, br, (0, 0, 255), 2)
            # 保存在本地
            cv2.imwrite(out, bg_cv)

        # 返回缺口的X坐标
        return tl[0]

    @classmethod
    def get_data_urls_by_img(cls, mediatype: str, data: Union[bytes, str]) -> str:
        """
        根据本地、远程或 bytes 内容的图片生成 Data URLs 格式的数据
        Data URLs 格式示例:
            data:image/png;base64,iVB...
            data:text/html,%3Ch1%3EHello%2C%20World%21%3C%2Fh1%3E

        关于 Data URLs 更多的描述，其参考文档: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs

        Args:
            mediatype: MIME 类型字符串，例如 'image/jpeg' JPEG 图像文件。
                如果省略，则默认为 text/plain;charset=US-ASCII
            data: 用于获取其 base64 编码的二进制数据
                参数格式可以为全路径图片，或 bytes 内容

        Returns:
            1). Data URLs 格式数据
        """
        assert type(data) in [
            str,
            bytes,
        ], "图片转 Data URLs 的参数 data 需要是全路径 str 或 bytes 数据"

        if isinstance(data, str):
            data_bytes = ReuseOperation.get_bytes_by_file(file_path=data)
            data_base64_encoded = EncryptOperation.base64_encode(encode_data=data_bytes)

        else:
            data_base64_encoded = EncryptOperation.base64_encode(encode_data=data)
        return f"data:image/{mediatype};base64,{data_base64_encoded}"
