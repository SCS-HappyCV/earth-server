from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
import traceback

from loguru import logger
from PIL import Image


def get_metadata(file_path: str | Path):
    # 获取图像元数据
    mode_to_bpp = {
        "1": 1,
        "L": 8,
        "P": 8,
        "RGB": 24,
        "RGBA": 32,
        "CMYK": 32,
        "YCbCr": 24,
        "I": 32,
        "F": 32,
    }
    with Image.open(file_path) as img:
        width, height = img.size
        channel_count = len(img.getbands())
        bit_depth = mode_to_bpp.get(img.mode, "Unknown")

    metadata = {
        "width": width,
        "height": height,
        "channel_count": channel_count,
        "bit_depth": bit_depth,
    }
    return metadata


def tiff2jpg(
    input_tiff_path: str | Path, output_jpg_path: str | Path | None = None
) -> str:
    if not output_jpg_path:
        # 如果输出路径不存在，创建一个临时文件来存储输出的JPG图片
        with NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            output_jpg_path = temp_file.name
            logger.warning(f"输出路径不存在，使用临时文件: {output_jpg_path}")

    # 将输入和输出路径转换为Path对象，并扩展用户路径
    input_path = Path(input_tiff_path).expanduser()
    output_path = Path(output_jpg_path).expanduser()

    # 检查输入文件是否存在，如果不存在则抛出异常
    if not input_path.is_file():
        err_msg = f"输入的TIFF图片文件 {input_path} 不存在。"
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    # 尝试打开输入的TIFF图片并转换为JPG格式
    try:
        logger.info(f"开始转换文件: {input_path}")
        with Image.open(input_path) as img:
            original_width, original_height = img.size
            logger.info(f"原始图片尺寸: {original_width}x{original_height}")

            # 如果图片尺寸大于1080p，则进行调整
            max_dimension = 1080
            if original_width > max_dimension or original_height > max_dimension:
                aspect_ratio = original_width / original_height
                if aspect_ratio > 1:  # 宽图
                    new_width = max_dimension
                    new_height = int(max_dimension / aspect_ratio)
                else:  # 高图
                    new_height = max_dimension
                    new_width = int(max_dimension * aspect_ratio)

                logger.info(f"调整图片尺寸为: {new_width}x{new_height}")
                img = img.resize((new_width, new_height), Image.LANCZOS)
            else:
                logger.info("图片尺寸不需要调整。")

            # 确保输出路径的父目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存图片为JPG格式
            img = img.convert("RGB")
            img.save(output_path, format="JPEG")
            logger.info(f"图片已成功转换并保存至: {output_path}")

    except Exception as e:
        logger.error(f"转换过程中出现错误: {e}")
        logger.debug(traceback.format_exc())
        raise

    else:
        return str(output_path)


# 日志配置
logger.add("tiff_to_png.log", format="{time} {level} {message}", level="DEBUG")

# 示例调用
if __name__ == "__main__":
    input_tiff = (
        "/data/openmmlab_data/Gid/gid_row/15image/GF2_PMS2__L1A0001471436-MSS2.tif"
    )
    output_jpg = "/data/tmp/a.jpg"
    try:
        output_file_path = tiff_to_jpg(input_tiff, output_jpg)
        logger.info(f"转换成功，输出文件路径: {output_file_path}")
    except Exception as e:
        logger.error(e)
