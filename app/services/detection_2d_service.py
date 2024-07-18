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
from app.utils.video_funcs import convert_video

from .object_service import ObjectService
from .project_service import ProjectService


class Detection2DService:
    def __init__(self, queries: Module, minio_client: Minio, redis_client: Redis):
        self.queries = queries
        self.project_service = ProjectService(queries, minio_client)
        self.object_service = ObjectService(queries, minio_client)
        self.redis_client = redis_client

    def create(
        self, image_id=None, video_id=None, project_id=None, project_name=None, **kwargs
    ):
        with self.queries.transaction() as tx:
            if project_id:
                project = self.project_service.get(project_id)
                if not project:
                    tx.rollback()

                    msg = f"Project with id {project_id} does not exist"
                    raise ValueError(msg)
            else:
                if video_id:
                    video_info = self.object_service.get_video(id=video_id)
                    video_info = Box(video_info)
                    cover_image_id = None
                elif image_id:
                    image_info = self.object_service.get_image(id=image_id)
                    image_info = Box(image_info)
                    cover_image_id = image_info.thumbnail_id or image_id
                else:
                    tx.rollback()

                    msg = "Either image_id or video_id must be provided"
                    raise ValueError(msg)

                project_id = self.project_service.create(
                    type="2d_detection",
                    name=project_name,
                    cover_image_id=cover_image_id,
                )

            last_id = self.queries.create_2d_detection(
                project_id=project_id, image_id=image_id, video_id=video_id
            )
            if not last_id:
                tx.rollback()

                msg = "Failed to create 2d detection"
                raise ValueError(msg)

        # 将任务推送到redis队列
        task_info = {"type": "2d_detection", "id": last_id, "project_id": project_id}
        push_task(self.redis_client, task_info)

        return task_info

    def get(self, *, id=None, project_id=None):
        if id or project_id:
            project = self.queries.get_2d_detection(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

        project = Box(project)
        if not project:
            logger.error(
                f"2D detection task not found: id={id}, project_id={project_id}"
            )
            return None

        logger.debug(f"2D detection task found: {project}")
        project = self.project_service._populate_project(project)

        return project

    def delete(self, id=None, project_id=None):
        if id or project_id:
            return self.queries.delete_2d_detection(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def run(self, id: int | None = None, project_id: int | None = None, **kwargs):
        """
        Run 2D detection task

        Args:
            id (int, optional): 2D detection task ID. Defaults to None.
            project_id (int, optional): Project ID. Defaults to None.
        """

        # 获取任务
        project_info = self.get(id=id, project_id=project_id)

        if not project_info:
            logger.error(
                f"detection 2D task not found: id={id}, project_id={project_id}"
            )
            return

        project_info = Box(project_info)

        logger.info(f"Running task: {project_info}")

        if project_info.image_id:
            data_info = self.object_service.get_image(id=project_info.image_id)
        elif project_info.video_id:
            data_info = self.object_service.get_video(id=project_info.video_id)
        else:
            logger.error("Neither image_id nor video_id found")
            return

        data_info = Box(data_info)

        logger.info(f"2d detection task data info: {data_info}")

        # 从 MinIO 复制图片到临时文件
        input_path = self.object_service.copy2local(data_info)

        # 在 input_path 的基础上生成输出路径
        output_path = input_path.with_stem(input_path.stem + "_raw_2d_det")
        if project_info.video_id:
            output_path = output_path.with_suffix(".mp4")

        # 获取 result_origin_name
        origin_name = Path(data_info.origin_name)
        result_origin_name = origin_name.with_stem(origin_name.stem + "_2d_det")
        if project_info.video_id:
            result_origin_name = result_origin_name.with_suffix(".mp4")

        # 运行预测脚本
        cmd = micromamba[
            "run",
            "-n",
            "zyb",
            "python",
            "/root/autodl-tmp/Zhaoyibei/2D_seg/yolo_det/track.py",
            "--input",
            input_path,
            "--output",
            output_path,
        ]

        logger.debug(f"Running command: {cmd}")
        cmd()
        logger.debug(f"2d detection task completed: {project_info}")

        # 保存输出文件
        if project_info.image_id:
            results = self.object_service.save_image(
                result_origin_name, output_path, origin_type="system"
            )
        elif project_info.video_id:
            # 视频转码
            output_raw_path = output_path
            output_path = output_raw_path.with_stem(input_path.stem + "_2d_det")

            convert_video(output_raw_path, output_path, codec="avc")
            results = self.object_service.save_video(
                result_origin_name, output_path, origin_type="system"
            )

        results = Box(results)
        logger.debug(f"2d detection results: {results}")

        # 设置plot_image_id和plot_video_id
        if project_info.image_id:
            plot_image_id = results.id
            plot_video_id = None
        elif project_info.video_id:
            plot_image_id = None
            plot_video_id = results.id

        # 更新数据库
        self.queries.complete_2d_detection(
            id=id,
            project_id=project_id,
            plot_image_id=plot_image_id,
            plot_video_id=plot_video_id,
        )

        # 删除临时文件
        Path(input_path).unlink(missing_ok=True)
        Path(output_path).unlink(missing_ok=True)
