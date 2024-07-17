from base64 import b64encode
import mimetypes
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
    POTREE_BASE_URL,
    POTREE_CLOUD_FOLDER,
    POTREE_SERVER_ROOT,
    POTREE_VIEWER_FOLDER,
    SHARE_LINK_BASE_URL,
    TMPDIR,
)
from app.utils.image_funcs import get_metadata, tiff2img
from app.utils.img2svg import ImageToSvgConverter
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
        self,
        name: str,
        file_path: Path,
        *,
        content_type: str | None = None,
        origin_type: str = "user",
        thumbnail_format: str = "jpg",
        mask_colors_map: dict | None = None,
        mask_color_mode: str = "rgb",
    ):
        if content_type is None:
            content_type = mimetypes.guess_type(file_path, strict=False)[0]

        # 保存图像文件到Minio并将元数据存储到数据库中
        image_info = self._save_image(
            name, file_path, content_type=content_type, origin_type=origin_type
        )
        image_info = Box(image_info)

        # 测试图像是否为tif格式，如果是则还要缩略图
        if content_type != "image/tiff":
            return Box(image_info=image_info)

        results = self._save_thumbnail(
            name,
            file_path,
            thumbnail_format=thumbnail_format,
            mask_colors_map=mask_colors_map,
            mask_color_mode=mask_color_mode,
        )

        # 更新对象的缩略图ID
        self.queries.update_thumbnail_id(
            object_id=image_info.object_id,
            thumbnail_image_id=results.thumbnail_info.image_id,
        )

        # 返回
        results.image_info = image_info
        return results

    def _save_thumbnail(
        self,
        name: str,
        file_path: Path,
        *,
        thumbnail_format: str = "jpg",
        mask_colors_map: dict = None,
        mask_color_mode: str = "rgb",
    ) -> dict | None:
        """
        保存缩略图文件到Minio并将元数据存储到数据库中

        :param name: 原对象名
        :param file_path: 原文件路径
        :param object_id: 原对象ID
        :param thumbnail_format: 缩略图格式
        :return: 保存的缩略图信息，如果保存失败则返回None
        """

        # 获取缩略图格式
        thumbnail_format = thumbnail_format.casefold()

        if mimetypes.guess_type(file_path, strict=False)[0] == "image/tiff":
            # 将tif格式的图像转换为缩略图
            thumbnail_path = tiff2img(file_path, output_format=thumbnail_format)

        # 保存缩略图到Minio并将元数据存储到数据库中
        thumbnail_name = Path(name).with_suffix(f".{thumbnail_format}")
        thumbnail_info = self._save_image(
            thumbnail_name, thumbnail_path, origin_type="thumbnail"
        )

        # 保存结果
        results = Box()
        results.thumbnail_info = thumbnail_info

        # # 校验结果
        # if not result:
        #     logger.error(f"更新文件的缩略图ID时发生错误: {result}")
        #     return None

        # 如果存在mask_colors_map，则根据缩略图生成对应的mask_svg图片
        if mask_colors_map:
            img2svg = ImageToSvgConverter(mask_colors_map, mask_color_mode)
            svg_name = Path(name).with_suffix(".svg")
            mask_svg_path = img2svg.convert(thumbnail_path)
            # 保存mask_svg到Minio并将元数据存储到数据库中
            mask_svg_info = self._save_image(
                svg_name,
                mask_svg_path,
                origin_type="mask_svg",
                content_type="image/svg+xml",
            )

            # 保存结果
            results.mask_svg_info = mask_svg_info

            # 删除临时文件
            mask_svg_path.unlink(missing_ok=True)

        # 删除临时文件
        thumbnail_path = Path(thumbnail_path)
        thumbnail_path.unlink(missing_ok=True)

        # 返回缩略图信息和mask_svg信息
        return results

    def _save_image(
        self,
        name: str,
        file_path: str | Path,
        *,
        origin_type: str,
        content_type: str | None = None,
    ) -> dict | None:
        """
        保存图像文件到Minio并将元数据存储到数据库中

        :param name: 文件名
        :param file_path: 文件路径
        :return: 保存的图像ID，如果保存失败则返回None
        """
        try:
            # 获取文件的内容类型
            if content_type is None:
                content_type = mimetypes.guess_type(file_path, strict=False)[0]

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
            metadata = {"origin_name": origin_name, "type": "image"}
            if content_type != "image/svg+xml":
                metadata |= get_metadata(file_path)
            else:
                # svg是矢量图，没有高宽等信息
                metadata |= {
                    "width": 0,
                    "height": 0,
                    "bit_depth": 0,
                    "channel_count": 0,
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
                name,
                folders,
                type="image",
                origin_name=origin_name,
                origin_type=origin_type,
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
        self,
        name: str,
        file_path: Path,
        content_type: str = "application/vnd.las",
        origin_type: str = "user",
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
                name,
                folders,
                type="pointcloud",
                origin_name=origin_name,
                origin_type=origin_type,
            )

            # 保存点云元数据到数据库
            pointcloud_id = self.queries.insert_pointcloud(
                object_id=object_id, **metadata
            )

            logger.info(f"成功保存点云: {name}, ID: {pointcloud_id}")
        except Exception as e:
            logger.error(f"保存点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None
        else:
            pointcloud_info = {"id": pointcloud_id, "object_id": object_id}
            return Box(pointcloud_info)

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

            object_data = Box(object_data)

            # 从Minio下载文件
            temp_file_path = Path(f"{TMPDIR}/{object_data.name}")
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
        origin_types: tuple[str] | None = None,
        offset: int | None = 0,
        row_count: int | None = 9999,
    ) -> BoxList | None:
        """
        获取所有对象元数据

        :param type: 对象类型
        :return: 包含对象元数据的BoxList对象，如果获取失败则返回None
        """
        try:
            origin_types = origin_types or ("user", "system")

            match type:
                case "image":
                    objects_data = self.queries.get_all_images(
                        offset=offset, row_count=row_count, origin_types=origin_types
                    )
                case "pointcloud":
                    objects_data = self.queries.get_all_pointclouds(
                        offset=offset, row_count=row_count, origin_types=origin_types
                    )
                case None | "all":
                    objects_data = self.queries.get_all_objects(
                        offset=offset, row_count=row_count, origin_types=origin_types
                    )

            if not objects_data:
                logger.warning(f"未找到类型为{type}的对象")
                return None

            objects_data = BoxList(objects_data)
            logger.debug(f"获取到的对象数据: {objects_data}")

            # 获取Minio对象的分享链接
            for object_data in objects_data:
                self._populate_object(object_data, should_thumbnail=True)

            logger.info(f"成功获取所有类型为{type}的对象")

            return objects_data
        except Exception as e:
            logger.error(f"获取对象时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def count(
        self,
        type: str | None = None,
        types: list[str] | None = None,
        origin_type: str | None = None,
        origin_types: list[str] | None = None,
    ) -> int:
        """
        获取对象数量

        :param type: 对象类型
        :return: 对象数量
        """
        try:
            if origin_type:
                origin_types = [origin_type]
            elif not (origin_type or origin_types):
                logger.warning("未提供对象来源类型")
                origin_types = ["user", "system"]

            if type:
                types = [type]
            elif not (type or types):
                logger.warning("未提供对象类型")
                types = ["image", "pointcloud"]

            count = self.queries.count_objects(types=types, origin_types=origin_types)

            return count
        except Exception as e:
            logger.error(f"获取对象数量时发生错误: {e}")
            logger.error(traceback.format_exc())

    def get_image(
        self,
        id: int = None,
        object_id=None,
        *,
        should_base64=False,
        should_thumbnail=True,
    ) -> Optional[Box]:
        """
        获取图像元数据和分享链接

        :param id: 图像ID
        :return: 包含图像元数据和分享链接的Box对象，如果获取失败则返回None
        """
        try:
            if id or object_id:
                image_data = self.queries.get_image(id=id, object_id=object_id)
            else:
                logger.warning("未提供ID或对象ID")
                return None

            if not image_data:
                logger.warning(f"未找到ID为{id}的图像")
                return None

            image_data = Box(image_data)
            logger.debug(f"获取到的图像数据: {image_data}")

            # 填充图像数据
            self._populate_object(
                image_data,
                should_base64=should_base64,
                should_thumbnail=should_thumbnail,
            )

            return image_data
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None

    def get_images(
        self,
        ids: list[int] | None = None,
        object_ids: list[int] | None = None,
        *,
        should_base64=False,
        should_thumbnail=True,
        only_thumbnail=False,
    ) -> BoxList | None:
        """
        获取多个图像元数据和分享链接

        :param ids: 图像ID列表
        :return: 包含图像元数据和分享链接的BoxList对象，如果获取失败则返回None
        """
        try:
            ids = ids or []
            object_ids = object_ids or []

            images_data = self.queries.get_images(ids=ids, object_ids=object_ids)
            if not images_data:
                logger.warning(f"未找到ID为{ids}的图像")
                return None

            images_data = BoxList(images_data)

            # 获取Minio对象的分享链接
            for image_data in images_data:
                # 填充图像数据
                self._populate_object(
                    image_data,
                    should_base64=should_base64,
                    should_thumbnail=should_thumbnail,
                    only_thumbnail=only_thumbnail,
                )

            logger.info(f"成功获取ID为{ids}的图像")
            return images_data
        except Exception as e:
            logger.error(f"获取图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return

    def _populate_object(
        self,
        object_data: dict,
        *,
        should_base64=False,
        should_thumbnail=False,
        only_thumbnail=False,
    ):
        """
        填充对象数据

        :param image_data: 对象数据
        :return: 填充后的对象数据
        """
        # only_thumbnail 为 True 时，隐含 should_thumbnail 为 True
        if only_thumbnail:
            should_thumbnail = True

        # 获取Minio对象的分享链接
        object_data["share_link"] = self._get_share_link(object_data)

        if should_thumbnail and object_data.get("thumbnail_id"):
            # 获取缩略图的分享链接
            thumbnail_data = self.queries.get_image(
                id=object_data["thumbnail_id"], object_id=None
            )
            object_data["thumbnail_link"] = self._get_share_link(thumbnail_data)

        # 获取对象和缩略图的Base64编码
        if should_base64:
            if should_thumbnail and object_data.get("thumbnail_id"):
                base64_thumbnail = self._get_base64_image(thumbnail_data)
                object_data["base64_thumbnail"] = base64_thumbnail

            if only_thumbnail and object_data.get("thumbnail_id"):
                # 如果只获取缩略图，而且缩略图存在，则不获取原图的Base64编码
                return object_data

            base64_image = self._get_base64_image(object_data)
            object_data["base64_image"] = base64_image

        return object_data

    def _get_base64_image(self, object_data: dict) -> str:
        """
        获取Minio对象的Base64编码

        :param object_data: 对象数据
        :return: Base64编码
        """
        try:
            logger.debug(f"获取Base64编码: {object_data}")

            # 获取Minio对象名
            object_name = get_object_name(object_data["name"], object_data["folders"])

            # 获取Base64编码
            base64_image = get_object_base64(
                self.minio_client, self.bucket_name, object_name
            )
            return base64_image
        except Exception as e:
            logger.error(f"获取Base64编码时发生错误: {e}")
            logger.error(traceback.format_exc())

    def _get_share_link(self, object_data: dict) -> None:
        """
        获取Minio对象的分享链接

        :param object_data: 对象数据
        :return: None
        """
        try:
            logger.debug(f"获取分享链接: {object_data}")

            # 获取Minio对象名
            object_name = get_object_name(object_data["name"], object_data["folders"])

            # 获取Minio对象的分享链接
            share_link = furl(f"{SHARE_LINK_BASE_URL}/{MINIO_BUCKET}/{object_name}").url
            return share_link
        except Exception as e:
            logger.error(f"获取分享链接时发生错误: {e}")
            logger.error(traceback.format_exc())

    def _populate_potree(self, object_data: dict, *, is_classified: bool):
        """
        填充对象数据的Potree分享链接

        :param object_data: 对象数据
        :return: 填充后的对象数据
        """
        try:
            # 利用etag生成唯一的临时文件名
            etag = object_data["etag"]
            tmp_file_path = f"{TMPDIR}/{etag}.las"

            # 获取Potree分享链接
            potree_link = furl(
                f"{POTREE_BASE_URL}/{POTREE_VIEWER_FOLDER}/{etag}.html"
            ).url

            # 检测生成文件是否已经存在
            potree_html_path = (
                Path(POTREE_SERVER_ROOT) / POTREE_VIEWER_FOLDER / f"{etag}.html"
            )
            if potree_html_path.is_file():
                logger.info(f"Potree文件已存在: {tmp_file_path}")
                object_data["potree_link"] = potree_link
                return object_data

            # 获取 Minio 对象名
            object_name = get_object_name(object_data["name"], object_data["folders"])

            # 从 Minio 下载文件
            self.minio_client.fget_object(self.bucket_name, object_name, tmp_file_path)

            # 运行 PotreePublisher
            is_classified = "--classified" if is_classified else "--no-classified"
            PotreePublisher[
                "--potree-server-root", POTREE_SERVER_ROOT, is_classified, tmp_file_path
            ]()

            # 填充对象数据
            object_data["potree_link"] = potree_link

        except Exception as e:
            logger.error(f"填充Potree分享链接时发生错误: {e}")
            logger.error(traceback.format_exc())
            raise
        else:
            return object_data
        finally:
            # 删除临时文件
            Path(tmp_file_path).unlink(missing_ok=True)

    def get_pointcloud(
        self,
        id: int | None = None,
        object_id: int | None = None,
        *,
        should_potree: bool = True,
    ) -> Optional[Box]:
        """
        获取点云元数据和分享链接

        :param id: 点云ID
        :return: 包含点云元数据和分享链接的Box对象，如果获取失败则返回None
        """
        try:
            if id or object_id:
                pointcloud_data = self.queries.get_pointcloud(
                    id=id, object_id=object_id
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
            if should_potree:
                is_classified = pointcloud_data.origin_type == "system"
                self._populate_potree(pointcloud_data, is_classified=is_classified)

            logger.info(f"成功获取点云: {pointcloud_data.name}, ID: {id}")
        except Exception as e:
            logger.error(f"获取点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None
        else:
            return pointcloud_data

    def delete_image(self, id: int | None = None, object_id: int | None = None) -> bool:
        """
        删除图像及其相关数据

        :param id: 图像ID
        :return: 删除是否成功
        """
        try:
            if not (id or object_id):
                logger.error("未提供ID或对象ID")
                return False

            image_data = self.queries.get_image(id=id, object_id=None)
            if not image_data:
                logger.warning(f"未找到ID为{id}, 对象ID为{object_id}的图像")
                return False

            # 从Minio删除文件
            object_name = get_object_name(image_data.name, image_data.folders)
            self.minio_client.remove_object(self.bucket_name, object_name)

            # 从数据库删除记录
            self.queries.delete_object(id=image_data.object_id)

            logger.info(
                f"成功删除图像: {image_data.name}, ID: {id}, 对象ID: {object_id}"
            )
            return True
        except Exception as e:
            logger.error(f"删除图像时发生错误: {e}")
            logger.error(traceback.format_exc())
            return False

    def delete_pointcloud(
        self, id: int | None = None, object_id: int | None = None
    ) -> bool:
        """
        删除点云及其相关数据

        :param id: 点云ID
        :return: 删除是否成功
        """
        try:
            if not (id or object_id):
                logger.error("未提供ID或对象ID")
                return False

            pointcloud_data = self.queries.get_pointcloud(id=id, object_id=object_id)
            if not pointcloud_data:
                logger.warning(f"未找到ID为{id}, 对象ID为{object_id}的点云")
                return False

            # 从Minio删除文件
            object_name = get_object_name(pointcloud_data.name, pointcloud_data.folders)
            self.minio_client.remove_object(self.bucket_name, object_name)

            # 从数据库删除记录
            self.queries.delete_object(id=pointcloud_data.object_id)

            logger.info(
                f"成功删除点云: {pointcloud_data.name}, ID: {id}, 对象ID: {object_id}"
            )
            return True
        except Exception as e:
            logger.error(f"删除点云时发生错误: {e}")
            logger.error(traceback.format_exc())
            return False

    def _save_object_metadata(
        self, name: str, folders: str, *, type: str, origin_name: str, origin_type: str
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
            origin_type=origin_type,
            type=type,
        )

        return object_id

    def copy2local(
        self, object_data: dict, output_path: str | Path | None = None
    ) -> Path | None:
        """
        将Minio对象复制到本地文件

        :param object_data: 对象数据
        :param output_path: 输出路径
        :return: 本地文件路径
        """
        try:
            # 获取Minio对象名
            object_name = get_object_name(object_data["name"], object_data["folders"])

            if output_path is None:
                # 生成临时命名文件
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=Path(object_name).suffix
                ) as temp_file:
                    temp_file_path = Path(temp_file.name)

                output_path = temp_file_path

            # 从Minio下载文件
            self.minio_client.fget_object(self.bucket_name, object_name, output_path)

            return output_path
        except Exception as e:
            logger.error(f"复制Minio对象到临时文件夹时发生错误: {e}")
            logger.error(traceback.format_exc())
            return None
