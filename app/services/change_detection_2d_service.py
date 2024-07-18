import json
import mimetypes
from pathlib import Path

from box import Box, BoxList
from loguru import logger
from minio import Minio
from plumbum.cmd import micromamba
from pugsql.compiler import Module
from redis import Redis

from app.config import SEGMENTATION_2D_BGR, TASK_QUEUE
from app.utils.tasks_funcs import push_task

from .object_service import ObjectService
from .project_service import ProjectService


class ChangeDetection2DService:
    def __init__(self, queries: Module, minio_client: Minio, redis_client: Redis):
        self.queries = queries
        self.project_service = ProjectService(queries, minio_client)
        self.object_service = ObjectService(queries, minio_client)
        self.redis_client = redis_client

    def create(
        self, image1_id, image2_id, project_id=None, project_name=None, **kwargs
    ):
        with self.queries.transaction() as tx:
            if project_id:
                project = self.project_service.get(project_id)
                if not project:
                    tx.rollback()

                    msg = f"Project with id {project_id} does not exist"
                    raise ValueError(msg)
            else:
                image_info = self.object_service.get_image(id=image1_id)
                image_info = Box(image_info)

                cover_image_id = image_info.thumbnail_id or image1_id

                project_id = self.project_service.create(
                    type="2d_change_detection",
                    name=project_name,
                    cover_image_id=cover_image_id,
                )

            last_id = self.queries.create_2d_change_detection(
                project_id=project_id, image1_id=image1_id, image2_id=image2_id
            )
            if not last_id:
                tx.rollback()

                msg = "Failed to create 2d segmentation"
                raise ValueError(msg)

        # 将任务推送到redis队列
        task_info = {
            "type": "2d_change_detection",
            "id": last_id,
            "project_id": project_id,
        }
        push_task(self.redis_client, task_info)

        return task_info

    def get(self, *, id=None, project_id=None):
        if id or project_id:
            project = self.queries.get_2d_change_detection(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

        project = Box(project)
        if not project:
            logger.error(
                f"2D change detection task not found: id={id}, project_id={project_id}"
            )
            return None

        logger.debug(f"2D change detection task found: {project}")
        project = self.project_service._populate_project(project)

        return project

    def delete(self, id=None, project_id=None):
        if id or project_id:
            return self.queries.delete_2d_change_detection(id=id, project_id=project_id)
        else:
            msg = "Either id or project_id must be provided"
            raise ValueError(msg)

    def run(self, id: int | None = None, project_id: int | None = None, **kwargs):
        """
        Run 2D change detection task

        Args:
            id (int, optional): 2D change detection task ID. Defaults to None.
            project_id (int, optional): Project ID. Defaults to None.
        """

        # 获取任务
        project_info = self.get(id=id, project_id=project_id)

        if not project_info:
            logger.error(
                f"2D change detection task not found: id={id}, project_id={project_id}"
            )
            return

        project_info = Box(project_info)

        image1_info = self.object_service.get_image(id=project_info.image1_id)
        image1_info = Box(image1_info)

        image1_origin_name = image1_info.origin_name
        image1_origin_name = Path(image1_origin_name)
        image1_origin_basename = image1_origin_name.stem

        plot_image_origin_basename = image1_origin_basename.split("_")[0] + "_result"
        plot_image_origin_name = plot_image_origin_basename + image1_origin_name.suffix

        logger.debug(f"plot_image_origin_name: {plot_image_origin_name}")

        plot_image_info = self.object_service.get_image(
            origin_name=plot_image_origin_name
        )

        logger.info(f"Running change detection 2D task: {project_info}")

        self.queries.complete_2d_change_detection(
            id=id,
            project_id=project_id,
            plot_image_id=plot_image_info.id,
            mask_image_id=None,
        )
        logger.info("Change detection 2D task completed")
