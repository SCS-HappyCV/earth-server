from base64 import b64encode
import os
from pathlib import Path
import shutil
import tempfile
import traceback
from typing import Optional

from box import Box, BoxList
from furl import furl
import laspy
from loguru import logger
from minio import Minio
from PIL import Image
import pillow_avif
from plumbum.cmd import PotreePublisher
from pugsql.compiler import Module

from app.config import (
    MINIO_BUCKET,
    POTREE_BASE_DIR,
    POTREE_BASE_URL,
    POTREE_CLOUD_FOLDER,
    POTREE_VIEWER_FOLDER,
    SHARE_LINK_BASE_URL,
)
from app.utils.image_funcs import get_metadata, tiff2jpg
from app.utils.object_funcs import (
    get_available_object_name,
    get_object_base64,
    get_object_name,
)
from app.utils.url import rewrite_base_url


class ObjectService:
    def __init__(self, queries: Module, minio_client: Minio):
        self.queries = queries
        self.minio_client = minio_client
        self.bucket_name = MINIO_BUCKET

    def save_image(
        self, name: str, file_path: Path, content_type: str = "image/jpeg"
    ) -> int | None:
        # 保存图像文件到Minio并将元数据存储到数据库中
        image_info = self._save_image(name, file_path, content_type)

        # 测试图像是否为tif格式，如果是则转换为jpg格式，保存为缩略图
        if content_type != "image/tiff":
            return image_info

        # 将tif格式的图像转换为jpg格式
        jpg_path = tiff2jpg(file_path)

        # 保存缩略图到Minio并将元数据存储到数据库中
        thumbnail_info = self._save_image(name, jpg_path, "image/jpeg")

        # 更新图像的缩略图ID
        thumbnail_info = Box(thumbnail_info)
        thumbnail_info.id = thumbnail_info.object_id
        del thumbnail_info["object_id"]
        result = self.queries.update_thumbnail_id(**thumbnail_info)

        # 校验结果
        if not result:
            logger.error(f"更新图像的缩略图ID时发生错误: {result}")
            return None

        # 删除临时文件
        jpg_path = Path(jpg_path)
        jpg_path.unlink(missing_ok=True)

        # 返回
        return image_info

    def _save_image(
        self, name: str, file_path: Path, content_type: str = "image/jpeg"
    ) -> dict | None:
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
            metadata = get_metadata(file_path)
            metadata |= {"origin_name": origin_name, "type": "image"}

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
            return {"image_id": image_id, "object_id": object_id}
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
                self._populate_object(object_data)

                if object_data.thumbnail_id is not None:
                    # 获取缩略图的分享链接
                    thumbnail_data = self.queries.get_object(
                        id=object_data.thumbnail_id
                    )
                    thumbnail_data = Box(thumbnail_data)
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

    def get_image(
        self, id: int = None, object_id=None, *, should_base64=False
    ) -> Optional[Box]:
        """
        获取图像元数据和分享链接

        :param id: 图像ID
        :return: 包含图像元数据和分享链接的Box对象，如果获取失败则返回None
        """
        try:
            if id:
                image_data = self.queries.get_image(id=id)
            elif object_id:
                image_data = self.queries.get_image_by_object_id(object_id=object_id)
            else:
                logger.warning("未提供ID或对象ID")
                return None

            if not image_data:
                logger.warning(f"未找到ID为{id}的图像")
                return None

            image_data = Box(image_data)
            logger.debug(f"获取到的图像数据: {image_data}")

            # 填充图像数据
            self._populate_object(image_data, should_base64=should_base64)

            return image_data
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get_images(self, ids: list[int], *, should_base64=False) -> BoxList | None:
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
                # 填充图像数据
                self._populate_object(image_data, should_base64=should_base64)

            logger.info(f"成功获取ID为{ids}的图像")
            return images_data
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return

    def _populate_object(
        self, object_data: dict, *, should_base64=False, should_thumbnail=False
    ) -> None:
        """
        填充对象数据

        :param image_data: 对象数据
        :return: None
        """

        # 获取Minio对象名
        object_name = get_object_name(object_data["name"], object_data["folders"])

        # 获取Minio对象的分享链接
        # share_link = self.minio_client.presigned_get_object(
        #     self.bucket_name, object_name
        # )
        # share_link = rewrite_base_url(share_link, SHARE_LINK_BASE_URL)

        share_link = furl(f"{SHARE_LINK_BASE_URL}/{MINIO_BUCKET}/{object_name}").url
        object_data["share_link"] = share_link

        if should_base64:
            # 获取对象的Base64编码
            base64_image = get_object_base64(
                self.minio_client, self.bucket_name, object_name
            )
            object_data["base64_image"] = base64_image

    def _populate_potree(self, object_data: dict) -> None:
        """
        填充对象数据的Potree分享链接

        :param object_data: 对象数据
        :return: None
        """
        try:
            # 利用etag生成唯一的临时文件名
            etag = object_data["etag"]
            tmp_file_path = f"/tmp/{etag}.las"

            # 获取Potree分享链接
            potree_link = furl(
                f"{POTREE_BASE_URL}/{POTREE_VIEWER_FOLDER}/{etag}.html"
            ).url

            # 检测生成文件是否已经存在
            potree_html_path = (
                Path(POTREE_BASE_DIR) / POTREE_VIEWER_FOLDER / f"{etag}.html"
            )
            if potree_html_path.is_file():
                logger.info(f"Potree文件已存在: {tmp_file_path}")
                object_data["potree_link"] = potree_link
                return

            # 获取Minio对象名
            object_name = get_object_name(object_data["name"], object_data["folders"])

            # 从Minio下载文件
            self.minio_client.fget_object(self.bucket_name, object_name, tmp_file_path)

            # 运行PotreePublisher
            PotreePublisher[tmp_file_path]()

            # 填充对象数据
            object_data["potree_link"] = potree_link

        except Exception as e:
            logger.error(f"填充Potree分享链接时发生错误: {e}")
            logger.error(traceback.format_exc())
            raise

        finally:
            # 删除临时文件
            Path(tmp_file_path).unlink(missing_ok=True)

    def get_pointcloud(
        self, id: int | None = None, object_id: int | None = None
    ) -> Optional[Box]:
        """
        获取点云元数据和分享链接

        :param id: 点云ID
        :return: 包含点云元数据和分享链接的Box对象，如果获取失败则返回None
        """
        try:
            if id:
                pointcloud_data = self.queries.get_pointcloud(id=id)
            elif object_id:
                pointcloud_data = self.queries.get_pointcloud_by_object_id(
                    object_id=object_id
                )
            else:
                logger.warning("未提供ID或对象ID")
                return None

            if not pointcloud_data:
                logger.warning(f"未找到ID为{id}的点云")
                return None

            pointcloud_data = Box(pointcloud_data)
            logger.debug(f"获取到的点云数据: {pointcloud_data}")

            # 填充点云数据
            self._populate_object(pointcloud_data)

            # 填充Potree分享链接
            self._populate_potree(pointcloud_data)

            logger.info(f"成功获取点云: {pointcloud_data.name}, ID: {id}")
            return pointcloud_data
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
            created_time=object_stat.last_modified,
            updated_time=object_stat.last_modified,
            modified_time=object_stat.last_modified,
            size=object_stat.size,
            content_type=object_stat.content_type,
            folders=folders,
            origin_name=origin_name,
            type=type,
        )

        return object_id
