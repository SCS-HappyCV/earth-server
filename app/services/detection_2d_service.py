import json
import mimetypes
from pathlib import Path

from box import Box, BoxList
from loguru import logger
from minio import Minio
from plumbum.cmd import micromamba
from pugsql.compiler import Module
from redis import Redis

from app.utils.tasks_funcs import push_task

from .object_service import ObjectService
from .project_service import ProjectService


class Detection2DService:
    def __init__(self, queries: Module, minio_client: Minio, redis_client: Redis):
        self.queries = queries
        self.project_service = ProjectService(queries, minio_client)
        self.object_service = ObjectService(queries, minio_client)
        self.redis_client = redis_client

    def create(self, image_id, project_id=None, project_name=None, **kwargs):
        with self.queries.transaction() as tx:
            if project_id:
                project = self.project_service.get(project_id)
                if not project:
                    tx.rollback()

                    msg = f"Project with id {project_id} does not exist"
                    raise ValueError(msg)
            else:
                image_info = self.object_service.get_image(id=image_id)
                image_info = Box(image_info)

                cover_image_id = image_info.thumbnail_id or image_id

                project_id = self.project_service.create(
                    type="2d_segmentation",
                    name=project_name,
                    cover_image_id=cover_image_id,
                )

            last_id = self.queries.create_2d_segmentation(
                project_id=project_id, image_id=image_id
            )
            if not last_id:
                tx.rollback()

                msg = "Failed to create 2d segmentation"
                raise ValueError(msg)

        # 将任务推送到redis队列
        task_info = {"type": "2d_segmentation", "id": last_id, "project_id": project_id}
        push_task(self.redis_client, task_info)

        return task_info

    def get(self, *, id=None, project_id=None):
        if id or project_id:
            project = self.queries.get_2d_segmentation(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

        project = Box(project)
        if not project:
            logger.error(
                f"2D segmentation task not found: id={id}, project_id={project_id}"
            )
            return None

        logger.debug(f"2D segmentation task found: {project}")
        project = self.project_service._populate_project(project)

        return project

    def delete(self, id=None, project_id=None):
        if id or project_id:
            return self.queries.delete_2d_segmentation(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def run(self, id: int | None = None, project_id: int | None = None, **kwargs):
        """
        Run 2D segmentation task

        Args:
            id (int, optional): 2D segmentation task ID. Defaults to None.
            project_id (int, optional): Project ID. Defaults to None.
        """

        # 获取任务
        project_info = self.get(id=id, project_id=project_id)

        if not project_info:
            logger.error(
                f"Segmentation 2D task not found: id={id}, project_id={project_id}"
            )
            return

        project_info = Box(project_info)

        logger.info(f"Running task: {project_info}")

        image_info = self.object_service.get_image(id=project_info.image_id)
        image_info = Box(image_info)

        logger.info(f"2d Seg task image info: {image_info}")

        # 从 MinIO 复制图片到临时文件
        input_path = self.object_service.copy2local(image_info)

        # 在 input_path 的基础上生成输出路径和掩码路径
        output_path = input_path.with_stem(input_path.stem + "_2d_seg")
        mask_path = input_path.with_stem(input_path.stem + "_2d_seg_mask")
        mask_path = mask_path.with_suffix(".png")

        # 获取 result_origin_name
        origin_name = Path(image_info.origin_name)
        result_origin_name = origin_name.with_stem(origin_name.stem + "_2d_seg").name

        # # 都转换为字符串
        # input_path = str(input_path)
        # output_path = str(output_path)
        # mask_path = str(mask_path)

        # 运行预测脚本
        micromamba[
            "run",
            "-n",
            "zyb",
            "python",
            "/root/autodl-tmp/Zhaoyibei/2D_seg/DPA/predict.py",
            "--inputimage",
            input_path,
            "--outputpath",
            output_path,
            "--maskpath",
            mask_path,
        ]()

        # 保存输出文件
        results = self.object_service.save_image(
            result_origin_name,
            output_path,
            origin_type="system",
            thumbnail_format="png",
            mask_colors_map=SEGMENTATION_2D_BGR,
            mask_color_mode="bgr",
        )
        results = Box(results)

        # 保存掩码文件
        # mask_info = self.object_service.save_image(
        #     result_origin_name, mask_path, origin_type="system"
        # )

        # 更新数据库
        image_info = results.image_info
        mask_svg_info = results.mask_svg_info
        self.queries.complete_2d_segmentation(
            id=id,
            project_id=project_id,
            plot_image_id=image_info.id,
            mask_image_id=None,
            mask_svg_id=mask_svg_info.id,
        )

        # 删除临时文件
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)
        Path(mask_path).unlink(missing_ok=True)
