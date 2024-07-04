import os
from pathlib import Path
import traceback
from typing import Optional

from box import Box
import laspy
from loguru import logger
from minio import Minio
import open3d as o3d
from PIL import Image
from pugsql.compiler import Module

from app.config import MINIO_BUCKET
from app.utils.object_funcs import get_available_object_name, get_object_name


class ObjectService:
    def __init__(self, queries: Module, minio_client: Minio):
        self.queries = queries
        self.minio_client = minio_client
        self.bucket_name = MINIO_BUCKET

    def save_image(
        self, name: str, file_path: Path, content_type: str = "image/jpeg"
    ) -> Optional[int]:
        """
        保存图像文件到Minio并将元数据存储到数据库中

        :param name: 文件名
        :param file_path: 文件路径
        :return: 保存的图像ID，如果保存失败则返回None
        """
        try:
            # 设置名称和路径
            folders = "images"
            origin_name = name

            # 获取可行的Minio对象名
            object_name = Path(folders) / name
            object_name = str(object_name)
            object_name = get_available_object_name(
                self.minio_client, self.bucket_name, object_name
            )
            name = Path(object_name).name

            # 获取图像元数据
            with Image.open(file_path) as img:
                width, height = img.size
                channel_count = len(img.getbands())

            metadata = {
                "width": width,
                "height": height,
                "channel_count": channel_count,
                "origin_name": origin_name,
            }

            # 上传文件到Minio
            self.minio_client.fput_object(
                self.bucket_name,
                object_name,
                str(file_path),
                content_type=content_type,
                metadata=metadata,
            )

            # 保存对象元数据到数据库
            object_id = self._save_object_metadata(name, folders, origin_name)

            # 保存图像元数据到数据库
            image_id = self.queries.insert_image(
                object_id=object_id,
                channel_count=channel_count,
                height=height,
                width=width,
            )

            logger.info(f"成功保存图像: {name}, ID: {image_id}")
            return image_id
        except Exception as e:
            logger.error(f"保存图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def save_pointcloud(
        self, name: str, file_path: Path, content_type: str = "application/vnd.las"
    ) -> Optional[int]:
        """
        保存点云文件到Minio并将元数据存储到数据库中

        :param name: 文件名
        :param file_path: 文件路径
        :param content_type: 内容类型
        :return: 保存的点云ID，如果保存失败则返回None
        """
        try:
            # 设置名称和路径
            folders = "pointclouds"
            origin_name = name

            # 获取可行的Minio对象名
            object_name = Path(folders) / name
            object_name = str(object_name)
            object_name = get_available_object_name(
                self.minio_client, self.bucket_name, object_name
            )
            name = Path(object_name).name

            # 读取点云文件
            las = laspy.read(file_path)
            point_count = las.header.point_count
            metadata = {"point_count": point_count, "origin_name": origin_name}

            # 上传文件到Minio
            self.minio_client.fput_object(
                self.bucket_name,
                object_name,
                str(file_path),
                content_type=content_type,
                metadata=metadata,
            )

            # 保存对象元数据到数据库
            object_id = self._save_object_metadata(name, folders, origin_name)

            # 保存点云元数据到数据库
            pointcloud_id = self.queries.insert_pointcloud(
                object_id=object_id, point_count=point_count
            )

            logger.info(f"成功保存点云: {name}, ID: {pointcloud_id}")
            return pointcloud_id
        except Exception as e:
            logger.error(f"保存点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get(self, id: int) -> Optional[Box]:
        """
        获取对象元数据和文件

        :param id: 对象ID
        :return: 包含对象元数据的Box对象，如果获取失败则返回None
        """
        try:
            object_data = self.queries.get_object(id=id)
            if not object_data:
                logger.warning(f"未找到ID为{id}的对象")
                return None

            # 从Minio下载文件
            temp_file_path = Path(f"/tmp/{object_data.name}")
            self.minio_client.fget_object(
                self.bucket_name, object_data.folders, str(temp_file_path)
            )

            result = Box({**object_data, "file_path": temp_file_path})
            logger.info(f"成功获取对象: {result.name}, ID: {id}")
            return result
        except Exception as e:
            logger.error(f"获取对象时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get_image(self, id: int) -> Optional[Box]:
        """
        获取图像元数据和分享链接

        :param id: 图像ID
        :return: 包含图像元数据和分享链接的Box对象，如果获取失败则返回None
        """
        try:
            image_data = self.queries.get_image(id=id)
            if not image_data:
                logger.warning(f"未找到ID为{id}的图像")
                return None

            object_data = self.queries.get_object(id=image_data.object_id)
            if not object_data:
                logger.warning(f"未找到与图像ID {id} 关联的对象")
                return None

            object_name = get_object_name(object_data.name, object_data.folders)
            # 获取Minio对象的分享链接
            share_link = self.minio_client.presigned_get_object(
                self.bucket_name, object_name
            )

            result = Box({**image_data, **object_data, "share_link": share_link})
            logger.info(f"成功获取图像: {result.name}, ID: {id}")
            return result
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get_pointcloud(self, id: int) -> Optional[Box]:
        """
        获取点云元数据和分享链接

        :param id: 点云ID
        :return: 包含点云元数据和分享链接的Box对象，如果获取失败则返回None
        """
        try:
            pointcloud_data = self.queries.get_pointcloud(id=id)
            if not pointcloud_data:
                logger.warning(f"未找到ID为{id}的点云")
                return None

            object_data = self.queries.get_object(id=pointcloud_data.object_id)
            if not object_data:
                logger.warning(f"未找到与点云ID {id} 关联的对象")
                return None

            # 获取Minio对象的分享链接
            share_link = self.minio_client.presigned_get_object(
                self.bucket_name,
                object_data.folders,
                expires=7 * 24 * 3600,  # 链接有效期7天
            )

            result = Box({**pointcloud_data, **object_data, "share_link": share_link})
            logger.info(f"成功获取点云: {result.name}, ID: {id}")
            return result
        except Exception as e:
            logger.error(f"获取点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def delete_image(self, id: int) -> bool:
        """
        删除图像及其相关数据

        :param id: 图像ID
        :return: 删除是否成功
        """
        try:
            image_data = self.queries.get_image(id=id)
            if not image_data:
                logger.warning(f"未找到ID为{id}的图像")
                return False

            object_data = self.queries.get_object(id=image_data.object_id)
            if not object_data:
                logger.warning(f"未找到与图像ID {id} 关联的对象")
                return False

            # 从Minio删除文件
            self.minio_client.remove_object(self.bucket_name, object_data.folders)

            # 从数据库删除记录
            self.queries.delete_image(id=id)
            self.queries.delete_object(id=object_data.id)

            logger.info(f"成功删除图像: {object_data.name}, ID: {id}")
            return True
        except Exception as e:
            logger.error(f"删除图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return False

    def delete_pointcloud(self, id: int) -> bool:
        """
        删除点云及其相关数据

        :param id: 点云ID
        :return: 删除是否成功
        """
        try:
            pointcloud_data = self.queries.get_pointcloud(id=id)
            if not pointcloud_data:
                logger.warning(f"未找到ID为{id}的点云")
                return False

            object_data = self.queries.get_object(id=pointcloud_data.object_id)
            if not object_data:
                logger.warning(f"未找到与点云ID {id} 关联的对象")
                return False

            # 从Minio删除文件
            self.minio_client.remove_object(self.bucket_name, object_data.folders)

            # 从数据库删除记录
            self.queries.delete_pointcloud(id=id)
            self.queries.delete_object(id=object_data.id)

            logger.info(f"成功删除点云: {object_data.name}, ID: {id}")
            return True
        except Exception as e:
            logger.error(f"删除点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return False

    def _save_object_metadata(self, name: str, folders: str, origin_name: str) -> int:
        """
        保存对象元数据到数据库

        :param name: 文件名
        :param folders: Minio中的对象的路径
        :return: 保存的对象ID
        """
        object_name = Path(folders) / name
        object_name = str(object_name)

        logger.info(
            f"保存对象元数据: {name}, 文件夹: {folders}, 原始名称: {origin_name}, 对象名: {object_name}"
        )
        object_stat = self.minio_client.stat_object(self.bucket_name, object_name)

        object_id = self.queries.insert_object(
            name=name,
            etag=object_stat.etag,
            modified_time=object_stat.last_modified,
            size=object_stat.size,
            content_type=object_stat.content_type,
            folders=folders,
            origin_name=origin_name,
        )

        return object_id

    def copy_object(self, source_id: int, new_name: str) -> Optional[int]:
        """
        复制对象

        :param source_id: 源对象ID
        :param new_name: 新对象名称
        :return: 新对象ID，如果复制失败则返回None
        """
        try:
            source_object = self.queries.get_object(id=source_id)
            if not source_object:
                logger.warning(f"未找到ID为{source_id}的源对象")
                return None

            new_object_name = f"{Path(source_object.folders).parent}/{new_name}"

            # 在Minio中复制对象
            result = self.minio_client.copy_object(
                self.bucket_name,
                new_object_name,
                f"{self.bucket_name}/{source_object.folders}",
            )

            # 在数据库中创建新对象记录
            new_object_id = self.queries.insert_object(
                name=new_name,
                etag=result.etag,
                modified_time=result.last_modified,
                size=source_object.size,
                content_type=source_object.content_type,
                folders=new_object_name,
            )

            logger.info(f"成功复制对象: {source_object.name} -> {new_name}")
            return new_object_id
        except Exception as e:
            logger.error(f"复制对象时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def move_object(self, object_id: int, new_folder: str) -> bool:
        """
        移动对象到新文件夹

        :param object_id: 对象ID
        :param new_folder: 新文件夹路径
        :return: 移动是否成功
        """
        try:
            object_data = self.queries.get_object(id=object_id)
            if not object_data:
                logger.warning(f"未找到ID为{object_id}的对象")
                return False

            old_object_name = object_data.folders
            new_object_name = f"{new_folder}/{Path(old_object_name).name}"

            # 在Minio中复制对象到新位置
            self.minio_client.copy_object(
                self.bucket_name,
                new_object_name,
                f"{self.bucket_name}/{old_object_name}",
            )

            # 删除旧对象
            self.minio_client.remove_object(self.bucket_name, old_object_name)

            # 更新数据库中的对象记录
            self.queries.update_object_folder(id=object_id, folders=new_object_name)

            logger.info(f"成功移动对象: {object_data.name} -> {new_object_name}")
            return True
        except Exception as e:
            logger.error(f"移动对象时发生错误: {e}")
            logger.error(traceback.format_exc())
            return False
