from pathlib import Path
import traceback

import laspy
from loguru import logger
import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d

# 配置loguru日志
logger.add("conversion.log", format="{time} {level} {message}", level="DEBUG")


def read_las_file(las_file_path: Path) -> o3d.geometry.PointCloud:
    """
    读取 las 文件并转换为 Open3D 的 PointCloud 格式

    参数:
    las_file_path (Path): las 文件路径

    返回:
    o3d.geometry.PointCloud: Open3D 点云对象
    """
    # 使用 laspy 读取 las 文件
    las = laspy.read(str(las_file_path))
    logger.info(f"成功读取 las 文件: {las_file_path}")

    # 提取点云数据
    points = np.vstack((las.x, las.y, las.z)).transpose()
    logger.info(f"点云数据形状: {points.shape}")

    # 检查点云数据
    if points.shape[0] == 0:
        err_msg = "点云数据为空"
        logger.error(err_msg)
        raise ValueError(err_msg)

    # 创建 Open3D 点云对象
    point_cloud = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    logger.info(f"成功转换 las 文件为 PointCloud")

    return point_cloud


def las_to_jpg(las_path: str, jpg_path: str) -> None:
    """
    将一个 las 格式的 3D 点云文件转换为 jpg 格式的 2D 图像文件。

    参数:
    las_path (str): las 文件路径
    jpg_path (str): jpg 文件路径
    """
    las_file_path = Path(las_path).expanduser()
    jpg_file_path = Path(jpg_path).expanduser()

    logger.info(f"开始处理文件: {las_file_path}")

    try:
        # 读取 las 文件并转换为 PointCloud
        pcd = read_las_file(las_file_path)

        # 设置渲染器
        width, height = 1920, 1080
        renderer = o3d.visualization.rendering.OffscreenRenderer(width, height)
        renderer.scene.set_background([1, 1, 1, 1])  # 背景设置为白色
        renderer.scene.add_geometry(
            "pcd", pcd, o3d.visualization.rendering.MaterialRecord()
        )

        # 设置相机参数
        center = np.mean(np.asarray(pcd.points), axis=0)
        bounds = pcd.get_axis_aligned_bounding_box()
        extent = np.linalg.norm(bounds.get_extent())
        fov = 60.0  # 视场角度
        renderer.setup_camera(fov, center, center + [0, 0, extent], [0, 1, 0])

        # 渲染图像
        image = renderer.render_to_image()
        logger.info("成功渲染图像")

        # 转换为 numpy 数组并保存为 jpg 文件
        image_np = np.asarray(image)
        plt.imsave(jpg_file_path, image_np)
        logger.info(f"成功保存图像到: {jpg_file_path}")

    except Exception as e:
        err_msg = f"处理文件时发生错误: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        raise


if __name__ == "__main__":
    import fire

    fire.Fire(las_to_jpg)
