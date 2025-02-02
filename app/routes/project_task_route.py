from typing import Any, ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post, put
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from loguru import logger

from app.schemas import ResponseWrapper
from app.schemas.respone_schema import Pagination
from app.services import get_services
from app.utils.connections_manager import ConnectionsManager


class ProjectTaskController(Controller):
    path = "/project"

    @get(path="/", sync_to_thread=True)
    def get(
        self,
        type: str | None = None,
        types: list[str] = (
            "2d_segmentation",
            "2d_detection",
            "2d_change_detection",
            "3d_segmentation",
        ),
        id: int | None = None,
        project_id: int | None = None,
        start: int | None = 0,
        length: int | None = 999,
    ) -> ResponseWrapper:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            project_service = services.project_service
            segmentation_2d_service = services.segmentation_2d_service
            detection_2d_service = services.detection_2d_service
            change_detection_2d_service = services.change_detection_2d_service
            segmentation_3d_service = services.segmentation_3d_service

            if not (type or id or project_id):
                # Get all projects
                logger.debug("Getting all projects")
                result = project_service.gets(
                    offset=start, row_count=length, types=types
                )
                total_count = project_service.count()

                if result is not None:
                    return ResponseWrapper(
                        Pagination(
                            total=total_count, start=start, length=length, data=result
                        )
                    )

                return Response(
                    ResponseWrapper(code=2, message="No projects found"),
                    status_code=HTTP_404_NOT_FOUND,
                )

            match type:
                case "2d_segmentation":
                    result = segmentation_2d_service.get(id=id, project_id=project_id)
                case "2d_detection":
                    result = detection_2d_service.get(id=id, project_id=project_id)
                case "2d_change_detection":
                    result = change_detection_2d_service.get(
                        id=id, project_id=project_id
                    )
                case "3d_segmentation":
                    result = segmentation_3d_service.get(id=id, project_id=project_id)
                case None:
                    result = project_service.get(project_id=project_id)
                    task_type = result["type"]
                    task_id = result["id"]

                    match task_type:
                        case "segmentation":
                            result = segmentation_2d_service.get(id=task_id)
                        case "detection":
                            result = detection_2d_service.get(id=task_id)
                        case "change_detection":
                            result = change_detection_2d_service.get(id=task_id)
                        case "segmentation_3d":
                            result = segmentation_3d_service.get(id=task_id)

                case _:
                    return Response(
                        ResponseWrapper(code=3, message="Invalid type"),
                        status_code=HTTP_400_BAD_REQUEST,
                    )

            logger.debug(f"Result: {result}")

            return ResponseWrapper(result)

    @put(path="/{id:int}", sync_to_thread=True)
    def update(self, data: dict, id: int) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            project_service = services.project_service

            logger.debug(f"Updating project with id {id}")

            if not data:
                return Response(
                    ResponseWrapper(code=3, message="Data is required"),
                    status_code=HTTP_404_NOT_FOUND,
                )

            result = project_service.update(id, **data)

            if not result:
                return Response(
                    ResponseWrapper(code=2, message=f"Project with id {id} not found"),
                    status_code=HTTP_404_NOT_FOUND,
                )

            return ResponseWrapper(message="Project updated successfully")

    @post(path="/", sync_to_thread=True)
    def create(self, data: dict) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            detection_2d_service = services.detection_2d_service
            change_detection_2d_service = services.change_detection_2d_service
            segmentation_2d_service = services.segmentation_2d_service
            segmentation_3d_service = services.segmentation_3d_service

            logger.debug(f"Creating 2d detection with data {data}")

            match data["type"]:
                case "2d_detection":
                    task_info = detection_2d_service.create(**data)
                case "2d_segmentation":
                    task_info = segmentation_2d_service.create(**data)
                case "2d_change_detection":
                    task_info = change_detection_2d_service.create(**data)
                case "3d_segmentation":
                    task_info = segmentation_3d_service.create(**data)
                case _:
                    raise ValidationException

            task_info = Box(task_info)
            if task_info.id:
                return ResponseWrapper(
                    task_info, message="Analysis task created successfully"
                )
            else:
                return Response(
                    ResponseWrapper(code=1, message="Failed to create project"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

    @delete(path="/", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete(
        self,
        id: int | None = None,
        type: str | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            segmentation_2d_service = services.segmentation_2d_service
            detection_2d_service = services.detection_2d_service
            change_detection_2d_service = services.change_detection_2d_service
            segmentation_3d_service = services.segmentation_3d_service
            project_service = services.project_service

            if not (id or project_id):
                return Response(
                    ResponseWrapper(code=3, message="Id is required"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            match type:
                case "2d_segmentation":
                    deleted_count = segmentation_2d_service.delete(
                        id=id, project_id=project_id
                    )
                case "2d_detection":
                    deleted_count = detection_2d_service.delete(
                        id=id, project_id=project_id
                    )
                case "2d_change_detection":
                    deleted_count = change_detection_2d_service.delete(
                        id=id, project_id=project_id
                    )
                case "3d_segmentation":
                    deleted_count = segmentation_3d_service.delete(
                        id=id, project_id=project_id
                    )
                case None:
                    deleted_count = project_service.delete(project_id)
                case _:
                    return Response(
                        ResponseWrapper(code=3, message="Invalid type"),
                        status_code=HTTP_400_BAD_REQUEST,
                    )

            if deleted_count:
                return ResponseWrapper(message="Analysis task deleted successfully")

            return Response(
                ResponseWrapper(code=2, message="Failed to delete project"),
                status_code=HTTP_400_BAD_REQUEST,
            )
