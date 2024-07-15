import json

from box import Box, BoxList
from minio import Minio
from pugsql.compiler import Module
from redis import Redis

from app.utils.table_funcs import delete_fields

from .project_service import ProjectService


class Detection2DService:
    def __init__(self, queries: Module, minio_client: Minio, redis_client: Redis):
        self.queries = queries
        self.project_service = ProjectService(queries, minio_client)
        self.redis_client = redis_client

    def create(self, image_id, project_id=None, name=None, **kwargs):
        with self.queries.transaction() as tx:
            if project_id:
                project = self.project_service.get(project_id)
                if not project:
                    tx.rollback()

                    msg = f"Project with id {project_id} does not exist"
                    raise ValueError(msg)
            else:
                project_id = self.project_service.create(
                    type="2d_detection", name=name, cover_image_id=image_id
                )

            last_id = self.queries.create_2d_detection(
                project_id=project_id, image_id=image_id
            )
            if not last_id:
                tx.rollback()

                msg = "Failed to create 2d detection"
                raise ValueError(msg)

        # 将任务发送到 Redis
        message = {"input_image_id": image_id, "id": last_id}
        self.redis_client.rpush(
            "2d_detections", json.dumps(message, ensure_ascii=False, indent="\t")
        )

        # 返回创建的 2D 检测的 ID 和项目 ID
        return last_id, project_id

    def get(self, *, id=None, project_id=None):
        if id:
            return self.queries.get_2d_detection(id=id)
        elif project_id:
            return self.queries.get_2d_detection_by_project_id(project_id=project_id)
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)

    def delete(self, id=None, project_id=None):
        if id:
            return self.queries.delete_2d_detection(id=id)
        elif project_id:
            return self.queries.delete_2d_detections_by_project_id(
                project_id=project_id
            )
        else:
            msg = "Either detection_id or project_id must be provided"
            raise ValueError(msg)
