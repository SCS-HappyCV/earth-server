import json
import mimetypes
from pathlib import Path

from box import Box, BoxList
from loguru import logger
from minio import Minio
from plumbum.cmd import micromamba
from pugsql.compiler import Module
from redis import Redis

from app.config import TASK_QUEUE
from app.utils.table_funcs import delete_fields

from .object_service import ObjectService
from .project_service import ProjectService


class Segmentation2DService:
    def __init__(self, queries: Module, minio_client: Minio, redis_client: Redis):
        self.queries = queries
        self.project_service = ProjectService(queries)
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
                project_id = self.project_service.create(
                    type="2d_segmentation", name=project_name, cover_image_id=image_id
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
        self.redis_client.rpush(
            TASK_QUEUE, json.dumps(task_info, ensure_ascii=False, indent="\t")
        )

        return last_id, project_id

    def get(self, *, id=None, project_id=None):
        if id:
            return self.queries.get_2d_segmentation(id=id)
        elif project_id:
            return self.queries.get_2d_segmentation_by_project_id(project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def delete(self, id=None, project_id=None):
        if id:
            return self.queries.delete_2d_segmentation(id=id)
        elif project_id:
            return self.queries.delete_2d_segmentations_by_project_id(
                project_id=project_id
            )
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def run(self, id: int | None = None, project_id: int | None = None):
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

        image_info = self.object_service.get_image(id=project_info.image_id)
        image_info = Box(image_info)

        # 从 MinIO 复制图片到临时文件
        input_path = self.object_service.copy2local(image_info)

        # 在 input_path 的基础上生成输出路径
        output_path = input_path.with_stem(input_path.stem + "_2d_seg")

        # 获取 result_origin_name
        result_origin_name = Path(image_info.origin_name).with_stem(
            image_info.origin_name.stem + "_2d_seg"
        )

        # 都转换为字符串
        input_path = str(input_path)
        output_path = str(output_path)

        # 运行预测脚本
        micromamba[
            "run",
            "-n",
            "openmmlab",
            "python",
            "/root/autodl-tmp/openmmlab/tools/predict.py",
            "--input_path",
            input_path,
            "--output_path",
            output_path,
        ]()

        # 保存输出文件
        image_info = self.object_service.save_image(result_origin_name, output_path)

        # 更新数据库
        self.queries.complete_2d_segmentation(
            id=id, plot_image_id=image_info["image_id"]
        )
