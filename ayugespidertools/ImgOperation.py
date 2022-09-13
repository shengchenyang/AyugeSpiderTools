#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    :  ImgOperation.py
@Time    :  2022/7/12 15:14
@Author  :  Ayuge
@Version :  1.0
@Contact :  ayuge.s@qq.com
@License :  (c)Copyright 2022-2023
@Desc    :  None
"""
import cv2
import requests
from PIL import Image
from ayugespidertools.config import NormalConfig
from ayugespidertools.common.MultiPlexing import ReuseOperation


__all__ = [
    'Picture',
]


class Picture(object):
    """
    对验证码图片的一些操作
    """

    @classmethod
    def get_captcha(cls, url: str):
        """
        下载完美滑块的图片，并将缺口图和滑块在一起的图片切割
        Args:
            url: 完美滑块的滑块图片链接

        Returns:
            None
        """
        session = requests.Session()
        session.headers = {
            'authority': 'captchas-1251008858.file.myqcloud.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        text = session.get(url).content
        with open(f'{NormalConfig.DOC_DIR}/captcha.png', 'wb') as f:
            f.write(text)

        # captcha = Image.new('RGB', (50, 120))  # 新建空白图片
        img = Image.open(f'{NormalConfig.DOC_DIR}/captcha.png')  # 实例化原始图片Image对象

        # 切割滑块验证码图片，将背景图和滑块图分开
        captcha = img.crop((260, 0, 325, 120 - 4))  # (left, upper, right, lower)
        # captcha = img.crop((274, 46, 300, 120 - 20))  # (left, upper, right, lower)
        captcha = captcha.convert('RGBA')
        captcha.save(f'{NormalConfig.DOC_DIR}/captcha_slide.png')

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
        '''
        # 图片大小为：334 159， 22 为 334 / 15 得到，58 是 159 /
        if index < 15:  # 完整的验证码图片是由30个小图片组合而成，共2行15列
            return (index * 22, 0)
        else:
            i = index - 15
            return (i * 22, 58)  # 每张小图的大小为22*58
        '''
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
    def recombine_captcha(cls, offset_list):
        """
        图片重组: 完美世界网站的图片重组方法
        Args:
            offset_list: 坐标列表

        Returns:
            None
        """
        captcha = Image.new('RGB', (13 * 20, 60 * 2 - 4))  # 新建空白图片
        img = Image.open(f'{NormalConfig.DOC_DIR}/captcha.png')  # 实例化原始图片Image对象

        # 切割滑块验证码图片，将背景图和滑块图分开
        captcha_de = img.crop((0, 0, 260, 120 - 4))  # (left, upper, right, lower)
        captcha_de = captcha_de.convert('RGBA')
        captcha_de.save(f'{NormalConfig.DOC_DIR}/captcha.png')

        for i, off in enumerate(offset_list):
            box = Picture.convert_css_to_offset(off)  # 根据css backgound-position获取每张小图的坐标
            regoin = img.crop(box)  # 抠图
            offset = Picture.convert_index_to_offset(i)  # 获取当前小图在空白图片的坐标
            captcha.paste(regoin, offset)  # 根据当前坐标将小图粘贴到空白图片
        captcha.save(f'{NormalConfig.DOC_DIR}/regoin.jpg')

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
        d = 120
        l = 20
        s = 9
        a = 61
        true_pic_list = []
        for curr_data in slide_data:
            curr_position_list = []
            if curr_data < l:
                curr_position_list.append(int(c / l * curr_data))
                curr_position_list.append(0)

            else:
                curr_position_list.append(int(c / l * (curr_data % l)))
                curr_position_list.append(60)

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
    def identify_gap(cls, bg, tp, out: str = None) -> int:
        """
        通过背景图片和缺口图片识别出滑块距离
        Args:
            bg: 背景图片，可以是图片的全路径，也可以是图片的 bytes 内容
            tp: 缺口（滑块）图片，可以是图片的全路径，也可以是图片的 bytes 内容
            out: 输出图片路径，示例：doc/test.jpg

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
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)  # 寻找最优匹配
        tl = max_loc  # 左上角点的坐标

        # 是否要输出绘制图像
        if out:
            # 绘制方框
            th, tw = tp_pic.shape[:2]
            br = (tl[0] + tw, tl[1] + th)  # 右下角点的坐标
            cv2.rectangle(bg_cv, tl, br, (0, 0, 255), 2)  # 绘制矩形
            cv2.imwrite(out, bg_cv)  # 保存在本地

        # 返回缺口的X坐标
        return tl[0]
