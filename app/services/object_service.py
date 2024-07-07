from base64 import b64encode
import os
from pathlib import Path
import traceback
from typing import Optional

from box import Box, BoxList
import laspy
from loguru import logger
from minio import Minio
from PIL import Image
import pillow_avif
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
                "origin_name": origin_name,
                "bit_depth": bit_depth,
                "type": "image",
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
            object_id = self._save_object_metadata(
                name, folders, origin_name, type="image"
            )

            # 保存图像元数据到数据库
            image_id = self.queries.insert_image(object_id=object_id, **metadata)

            logger.info(f"成功保存图像: {name}, ID: {image_id}")
            return image_id, object_id
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
            metadata = {
                "point_count": point_count,
                "origin_name": origin_name,
                "type": "pointcloud",
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
            object_id = self._save_object_metadata(
                name, folders, origin_name, type="pointcloud"
            )

            # 保存点云元数据到数据库
            pointcloud_id = self.queries.insert_pointcloud(
                object_id=object_id, **metadata
            )

            logger.info(f"成功保存点云: {name}, ID: {pointcloud_id}")
            return pointcloud_id, object_id
        except Exception as e:
            logger.error(f"保存点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def delete(self, id) -> bool:
        """
        删除对象及其相关数据

        :param id: 对象ID
        :return: 删除是否成功
        """
        try:
            object_data = self.queries.get_object(id=id)
            if not object_data:
                logger.warning(f"未找到ID为{id}的对象")
                return False

            object_data = Box(object_data)

            # 从Minio删除文件
            object_name = get_object_name(object_data.name, object_data.folders)
            self.minio_client.remove_object(self.bucket_name, object_name)

            # 从数据库删除记录
            result = self.queries.delete_object(id=id)

            if result:
                logger.info(f"成功删除对象: {object_data.name}, ID: {id}")
                return True
            else:
                logger.warning(f"删除对象失败: {object_data.name}, ID: {id}")
                return False
        except Exception as e:
            logger.error(f"删除对象时发生错误: {e}")
            logger.error(traceback.format_exc())
            return False

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

    def gets(
        self,
        type: str | None = None,
        origin_types: tuple[str] = ("user", "system"),
        offset: int | None = 0,
        row_count: int | None = 9999,
    ) -> BoxList | None:
        """
        获取所有对象元数据

        :param type: 对象类型
        :return: 包含对象元数据的BoxList对象，如果获取失败则返回None
        """
        try:
            match type:
                case "image":
                    objects_data = self.queries.get_images(
                        offset=offset, row_count=row_count, origin_types=origin_types
                    )
                case "pointcloud":
                    objects_data = self.queries.get_pointclouds(
                        offset=offset, row_count=row_count, origin_types=origin_types
                    )
                case None | "all":
                    objects_data = self.queries.get_objects(
                        offset=offset, row_count=row_count, origin_types=origin_types
                    )

            if not objects_data:
                logger.warning(f"未找到类型为{type}的对象")
                return None

            objects_data = BoxList(objects_data)
            logger.debug(f"获取到的对象数据: {objects_data}")

            # 获取Minio对象的分享链接
            for object_data in objects_data:
                object_name = get_object_name(object_data.name, object_data.folders)
                share_link = self.minio_client.presigned_get_object(
                    self.bucket_name, object_name
                )
                object_data.share_link = share_link

                if object_data.thumbnail_id is not None:
                    # 获取缩略图的分享链接
                    thumbnail_data = self.queries.get_object(
                        id=object_data.thumbnail_id
                    )
                    thumbnail_name = get_object_name(
                        thumbnail_data.name, thumbnail_data.folders
                    )
                    thumbnail_link = self.minio_client.presigned_get_object(
                        self.bucket_name, thumbnail_name
                    )
                    object_data.thumbnail_link = thumbnail_link

            logger.info(f"成功获取所有类型为{type}的对象")

            return objects_data
        except Exception as e:
            logger.error(f"获取对象时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get_image(self, id: int, *, should_base64=False) -> Optional[Box]:
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

            image_data = Box(image_data)
            logger.debug(f"获取到的图像数据: {image_data}")

            object_name = get_object_name(image_data.name, image_data.folders)

            # 获取Minio对象的分享链接
            share_link = self.minio_client.presigned_get_object(
                self.bucket_name, object_name
            )
            result = Box({**image_data, "share_link": share_link})
            logger.debug(f"成功获取图像: {result.name}, ID: {id}")

            if should_base64:
                # 获取图像的Base64编码
                response = self.minio_client.get_object(self.bucket_name, object_name)
                data = response.read()
                base64_image = b64encode(data).decode("utf-8")
                result.base64_image = base64_image
                logger.debug("成功获取图像的Base64编码")

            return result
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get_images(self, ids: list[int]) -> BoxList | None:
        """
        获取多个图像元数据和分享链接

        :param ids: 图像ID列表
        :return: 包含图像元数据和分享链接的BoxList对象，如果获取失败则返回None
        """
        try:
            images_data = self.queries.get_images_by_ids(ids=ids)
            if not images_data:
                logger.warning(f"未找到ID为{ids}的图像")
                return None

            images_data = BoxList(images_data)

            # 获取Minio对象的分享链接
            for image_data in images_data:
                object_name = get_object_name(image_data.name, image_data.folders)
                share_link = self.minio_client.presigned_get_object(
                    self.bucket_name, object_name
                )
                image_data.share_link = share_link

            logger.info(f"成功获取ID为{ids}的图像")
            return images_data
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return

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

            pointcloud_data = Box(pointcloud_data)
            logger.debug(f"获取到的点云数据: {pointcloud_data}")

            object_name = get_object_name(pointcloud_data.name, pointcloud_data.folders)

            # 获取Minio对象的分享链接
            share_link = self.minio_client.presigned_get_object(
                self.bucket_name, object_name
            )

            logger.debug(f"分享链接: {share_link}")

            result = Box({**pointcloud_data, "share_link": share_link})
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

    def _save_object_metadata(
        self, name: str, folders: str, origin_name: str, type: str
    ) -> int:
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
            type=type,
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
