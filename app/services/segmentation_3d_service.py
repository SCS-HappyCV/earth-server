import json
import mimetypes
from pathlib import Path

from box import Box, BoxList
from dotenv import load_dotenv
from loguru import logger
from minio import Minio
from plumbum.cmd import micromamba
from pugsql.compiler import Module
from redis import Redis

from app.config import TASK_QUEUE, TMPDIR
from app.utils.table_funcs import delete_fields
from app.utils.tasks_funcs import push_task

from .object_service import ObjectService
from .project_service import ProjectService


class Segmentation3DService:
    def __init__(self, queries: Module, minio_client: Minio, redis_client: Redis):
        self.queries = queries
        self.project_service = ProjectService(queries, minio_client)
        self.object_service = ObjectService(queries, minio_client)
        self.redis_client = redis_client

    def create(self, pointcloud_id, project_id=None, project_name=None, **kwargs):
        with self.queries.transaction() as tx:
            if project_id:
                project = self.project_service.get(project_id)
                if not project:
                    tx.rollback()

                    msg = f"Project with id {project_id} does not exist"
                    raise ValueError(msg)
            else:
                pointcloud_info = self.object_service.get_pointcloud(id=pointcloud_id)
                pointcloud_info = Box(pointcloud_info)

                cover_image_id = pointcloud_info.thumbnail_id

                project_id = self.project_service.create(
                    type="3d_segmentation",
                    name=project_name,
                    cover_image_id=cover_image_id,
                )

            last_id = self.queries.create_3d_segmentation(
                project_id=project_id, pointcloud_id=pointcloud_id
            )
            if not last_id:
                tx.rollback()

                msg = "Failed to create 3d segmentation"
                raise ValueError(msg)

        # 将任务推送到redis队列
        task_info = {"type": "3d_segmentation", "id": last_id, "project_id": project_id}
        push_task(self.redis_client, task_info)

        return task_info

    def get(self, *, id=None, project_id=None):
        if id or project_id:
            project = self.queries.get_3d_segmentation(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

        project = Box(project)
        if not project:
            logger.error(
                f"3D segmentation task not found: id={id}, project_id={project_id}"
            )
            return None

        logger.debug(f"3D segmentation task found: {project}")
        project = self.project_service._populate_project(project)

        return project

    def delete(self, id=None, project_id=None):
        if id or project_id:
            return self.queries.delete_3d_segmentation(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def run(self, id: int | None = None, project_id: int | None = None, **kwargs):
        """
        Run 3D segmentation task

        Args:
            id (int, optional): 3D segmentation task ID. Defaults to None.
            project_id (int, optional): Project ID. Defaults to None.
        """

        # 获取任务
        project_info = self.get(id=id, project_id=project_id)

        if not project_info:
            logger.error(
                f"Segmentation 3D task not found: id={id}, project_id={project_id}"
            )
            return

        project_info = Box(project_info)

        logger.info(f"Running task: {project_info}")

        pointcloud_info = self.object_service.get_pointcloud(
            id=project_info.pointcloud_id
        )

        logger.info(f"3D Seg task image info: {pointcloud_info}")

        # 从 MinIO 复制文件到临时文件
        input_path = self.object_service.copy2local(pointcloud_info)

        # 在 input_path 的基础上生成输出路径和掩码路径
        output_path = input_path.with_stem(input_path.stem + "_3d_seg")
        output_path = output_path.with_stem(output_path.stem + "_3d_seg")

        # 获取 result_origin_name
        origin_name = Path(pointcloud_info.origin_name)
        result_origin_name = origin_name.with_stem(origin_name.stem + "_3d_seg").name

        # # 都转换为字符串
        # input_path = str(input_path)
        # output_path = str(output_path)
        # mask_path = str(mask_path)

        log_dir = f"{TMPDIR}/3d/logs"
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        # 运行预测脚本
        cmd = micromamba[
            "run",
            "-n",
            "3d",
            "python",
            "/root/autodl-tmp/Zhaoyibei/3D_dection/Zhongshui_inference/inference.py",
            "--test_area",
            "4",
            "--visual",
            "--input_path",
            input_path,
            "--output_path",
            output_path,
        ]
        logger.info(f"Running command: {cmd}")
        cmd()
        logger.debug(f"3D segmentation result saved to {output_path}")

        # 保存输出文件
        result_pointcloud_info = self.object_service.save_pointcloud(
            result_origin_name, output_path, origin_type="system"
        )

        # 更新数据库
        self.queries.complete_3d_segmentation(
            id=id, project_id=project_id, result_pointcloud_id=result_pointcloud_info.id
        )

        # 删除临时文件
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)
