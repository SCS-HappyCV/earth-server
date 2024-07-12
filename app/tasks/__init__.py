from threading import Event

from box import Box
from loguru import logger
from minio import Minio
from pugsql.compiler import Module
from redis import Redis

from app.services import Segmentation2DService


def background_tasks(
    stop_event: Event, redis_client: Redis, queries: Module, minio_client: Minio
):
    while not stop_event.is_set():
        _, task_info = redis_client.blpop("tasks")
        task_info = Box().from_json(task_info)

        segmentation_2d_service = Segmentation2DService(queries, minio_client)

        match task_info.type:
            case "2d_detection":
                ...
            case "2d_change_detection":
                ...
            case "2d_segmentation":
                segmentation_2d_service.run(id=task_info.id)
            case "3d_segmentation":
                ...
            case _:
                logger.error(f"Unknown task type: {task_info.type}")

    redis_client.close()
    queries.disconnect()

    logger.info("Background tasks stopped")
