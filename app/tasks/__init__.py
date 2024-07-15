import json
from threading import Event, Thread
import traceback

from box import Box, BoxList
from loguru import logger
from minio import Minio
import pugsql
from redis import Redis

from app.config import (
    DB_URI,
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    QUERIES_PATH,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PORT,
    TASK_QUEUE,
)
from app.services import ProjectService, Segmentation2DService
from app.utils.tasks_funcs import push_task


class BackgroudTasksService:
    def __init__(self):
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        queries = pugsql.module(QUERIES_PATH)
        queries.connect(DB_URI)
        minio_client = Minio(
            MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False
        )

        self.project_service = ProjectService(queries, minio_client)
        self.segmentation_2d_service = Segmentation2DService(
            queries, minio_client, redis_client
        )

        self.queries = queries
        self.redis_client = redis_client
        self.stop_event = Event()

    def background_tasks(self):
        while not self.stop_event.is_set():
            try:
                task_info = self.get_task()
                self.run_task(task_info)
            except Exception as e:
                logger.error(f"Error running task: {e}")
                logger.error(traceback.format_exc())

    def push_tasks(self):
        projects = self.project_service.gets(statuses=("waiting", "running"))
        projects = BoxList(projects)
        logger.info(f"Found non-completed projects: {projects}")

        for project in projects:
            project.project_id = project.id
            project.id = None
            push_task(self.redis_client, project)

    def start(self):
        logger.info("Starting background tasks")
        logger.info("Pushing tasks to queue")
        self.push_tasks()
        logger.info("Tasks pushed to queue")
        thread = Thread(target=self.background_tasks)
        thread.start()
        logger.info("Background tasks started")

    def stop(self):
        logger.info("Stopping background tasks")

        self.stop_event.set()
        self.redis_client.close()
        self.queries.disconnect()

        logger.info("Background tasks stopped")

    def get_task(self):
        _, task_info = self.redis_client.blpop(TASK_QUEUE)
        task_info = task_info.decode("utf-8")
        task_info = Box().from_json(task_info)

        return task_info

    def run_task(self, task_info: Box):
        logger.info(f"Running task: {task_info.id}")

        match task_info.type:
            case "2d_detection":
                ...
            case "2d_change_detection":
                ...
            case "2d_segmentation":
                logger.info(f"Running 2D segmentation task: {task_info.id}")
                self.segmentation_2d_service.run(**task_info)
            case "3d_segmentation":
                ...
            case _:
                logger.error(f"Unknown task type: {task_info.type}")
