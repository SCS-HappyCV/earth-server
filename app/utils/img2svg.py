from collections import OrderedDict
from pathlib import Path
import shutil
import traceback
from typing import Iterable

from box import Box
import cv2 as cv
import einops as ep
from fire import Fire
from loguru import logger
import numpy as np
import svgwrite


class ImageToSvgConverter:
    def __init__(self, colors_map: dict[str, Iterable], color_mode: str = "rgb"):
        """
        初始化转换器

        :param colors_map: 颜色映射表
        """
        # 颜色模式
        color_mode = color_mode.casefold()
        if color_mode not in ["rgb", "bgr"]:
            msg = "颜色模式必须为rgb或bgr"
            raise ValueError(msg)

        # 把key的字符串的空白字符去掉，转化为-连接的字符串
        colors_map = {k.strip().replace(" ", "-"): v for k, v in colors_map.items()}

        # 根据颜色模式调整颜色顺序
        if color_mode == "bgr":
            self.colors_map = {k: v[::-1] for k, v in colors_map.items()}

        # 保存到OrderedDict中，保持顺序
        self.colors_map = OrderedDict(self.colors_map)

    def colors2channels(self, img: np.ndarray) -> np.ndarray:
        """
        将多类别的rgb图转换为多通道二值图

        :param img: 输入图像
        :return: 多通道二值图
        """
        logger.info("正在将RGB图像转换为多通道二值图")
        binary_images = []
        for color in self.colors_map.values():
            color = color[::-1]  # 转换颜色顺序为BGR
            mask = cv.inRange(img, color, color)
            binary_images.append(mask)
        return np.array(binary_images)

    def get_contours_list(self, bin_imgs: np.ndarray) -> list:
        """
        对多通道二值图搜索轮廓

        :param bin_imgs: 多通道二值图
        :return: 轮廓列表
        """
        logger.info("正在搜索轮廓")
        contours_list = []
        for bin_img in bin_imgs:
            contours, _ = cv.findContours(
                bin_img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
            )
            contours_list.append(contours)
        return contours_list

    def contours2svg(self, contours_list: list, filename: str):
        """
        将轮廓转换为SVG格式，并对每组轮廓设置对应颜色

        :param contours_list: 轮廓列表
        :param filename: 输出文件名
        """
        logger.info(f"正在生成SVG文件: {filename}")
        dwg = svgwrite.Drawing(filename, id="mask-svg")

        for contours, (label, color) in zip(contours_list, self.colors_map.items()):
            if not contours:
                continue

            color_str = f"rgb{tuple(color)}"
            for c in contours:
                points = c.reshape(-1, 2).tolist()
                polygon = dwg.polygon(
                    points=points,
                    fill=color_str,
                    # fill_opacity=0,
                    stroke=color_str,
                    stroke_width=1,
                    stroke_linejoin="round",
                    class_=label,
                )
                dwg.add(polygon)

        # dwg.embed_stylesheet(
        #     """
        #     polygon:hover {
        #         fill-opacity: 0.5;
        #     }
        #     """
        # )
        dwg.save()

    def convert(self, input_path: str | Path, output_path: str | Path | None = None):
        """
        将PNG图像转换为SVG

        :param input_path: 输入PNG文件路径
        :param output_path: 输出SVG文件路径
        """
        try:
            input_path = Path(input_path).expanduser().resolve()

            if output_path is None:
                output_path = input_path.with_suffix(".svg")
            else:
                output_path = Path(output_path).expanduser().resolve()

            logger.info(f"正在处理图像: {input_path}")
            img = cv.imread(str(input_path))

            colors = self.colors_map.values()
            # colors.shape = (n, 3)

            bin_imgs = self.colors2channels(img)
            contours_list = self.get_contours_list(bin_imgs)
            self.contours2svg(contours_list, str(output_path))

            logger.success(f"转换完成，SVG文件已保存到: {output_path}")

            return output_path
        except Exception as e:
            logger.error(f"转换过程中发生错误: {e}")
            logger.error(f"错误详情:\n{traceback.format_exc()}")
            raise


def main(colors_map: dict, input_path: str, output_path: str):
    """
    主函数

    :param config_path: 配置文件路径
    :param input_path: 输入JPG文件路径
    :param output_path: 输出SVG文件路径
    """
    converter = ImageToSvgConverter(colors_map)
    converter.convert(input_path, output_path)


if __name__ == "__main__":
    import sys

    sys.path.extend([".", ".."])

    from app.config import SEGMENTATION_2D_BGR

    converter = ImageToSvgConverter(SEGMENTATION_2D_BGR, "BGR")
    converter.convert(
        "/root/autodl-tmp/tmp/GF2_PMS1__L1A0001680851-MSS1_2d_seg.png",
        "/root/autodl-tmp/tmp/GF2_PMS1__L1A0001680851-MSS1_2d_seg.svg",
    )
