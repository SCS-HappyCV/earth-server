from threading import Event, Thread
import traceback

from box import Box, BoxList
from loguru import logger

from app.services import get_services
from app.utils.connections_manager import ConnectionsManager
from app.utils.tasks_funcs import get_task, push_task


class BackgroudTasksService:
    def __init__(self):
        self.connections_manager = ConnectionsManager()
        self.connections_manager.open()

        self.services = get_services(
            self.connections_manager.queries,
            self.connections_manager.minio_client,
            self.connections_manager.redis_client,
        )
        self.project_service = self.services.project_service
        self.segmentation_2d_service = self.services.segmentation_2d_service
        self.segmentation_3d_service = self.services.segmentation_3d_service

        self.stop_event = Event()

    def background_tasks(self):
        while not self.stop_event.is_set():
            try:
                task_info = get_task(self.connections_manager.redis_client)
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
            push_task(self.connections_manager.redis_client, project)

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
        self.connections_manager.close()

        logger.info("Background tasks stopped")

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
                logger.info(f"Running 3D segmentation task: {task_info.id}")
                self.segmentation_3d_service.run(**task_info)
            case _:
                logger.error(f"Unknown task type: {task_info.type}")
