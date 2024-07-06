from typing import Any, ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post
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
from app.services import (
    ChangeDetection2DService,
    Detection2DService,
    ProjectService,
    Segmentation2DService,
    Segmentation3DService,
)


def detection_2d_service_provider(state: State) -> Detection2DService:
    return Detection2DService(state.queries)


def change_detection_2d_service_provider(state: State) -> ChangeDetection2DService:
    return ChangeDetection2DService(state.queries)


def segmentation_2d_service_provider(state: State) -> Segmentation2DService:
    return Segmentation2DService(state.queries)


def segmentation_3d_service_provider(state: State) -> Segmentation3DService:
    return Segmentation3DService(state.queries)


def project_service_provider(state: State) -> ProjectService:
    return ProjectService(state.queries)


class ProjectTaskController(Controller):
    path = "/task"
    dependencies: ClassVar = {
        "detection_2d_service": Provide(
            detection_2d_service_provider, sync_to_thread=False
        ),
        "change_detection_2d_service": Provide(
            change_detection_2d_service_provider, sync_to_thread=False
        ),
        "segmentation_2d_service": Provide(
            segmentation_2d_service_provider, sync_to_thread=False
        ),
        "segmentation_3d_service": Provide(
            segmentation_3d_service_provider, sync_to_thread=False
        ),
        "project_service": Provide(project_service_provider, sync_to_thread=False),
    }

    @get(path="/", sync_to_thread=True)
    def get(
        self,
        segmentation_2d_service: Segmentation2DService,
        detection_2d_service: Detection2DService,
        change_detection_2d_service: ChangeDetection2DService,
        segmentation_3d_service: Segmentation3DService,
        project_service: ProjectService,
        type: str | None = None,
        id: int | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper:
        logger.debug("Getting 2d segmentation tasks")

        match type:
            case "2d_segmentation":
                result = segmentation_2d_service.get(id=id, project_id=project_id)
            case "2d_detection":
                result = detection_2d_service.get(id=id, project_id=project_id)
            case "2d_change_detection":
                result = change_detection_2d_service.get(id=id, project_id=project_id)
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
                raise ValidationException

        logger.debug(f"Result: {result}")

        return ResponseWrapper(result)

    @post(path="/", sync_to_thread=True)
    def create(
        self,
        data: dict,
        detection_2d_service: Detection2DService,
        change_detection_2d_service: ChangeDetection2DService,
        segmentation_2d_service: Segmentation2DService,
        segmentation_3d_service: Segmentation3DService,
    ) -> ResponseWrapper | Response:
        logger.debug(f"Creating 2d detection with data {data}")

        match data["type"]:
            case "2d_detection":
                task_id, project_id = detection_2d_service.create(**data)
            case "2d_segmentation":
                task_id, project_id = segmentation_2d_service.create(**data)
            case "2d_change_detection":
                task_id, project_id = change_detection_2d_service.create(**data)
            case "3d_segmentation":
                task_id, project_id = segmentation_3d_service.create(**data)
            case _:
                raise ValidationException

        if task_id:
            return ResponseWrapper(
                {"id": task_id, "type": data["type"], "project_id": project_id},
                message="Analysis task created successfully",
            )
        else:
            return Response(
                ResponseWrapper(code=1, message="Failed to create project"),
                status_code=HTTP_400_BAD_REQUEST,
            )

    @delete(path="/", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete(
        self,
        detection_2d_service: Detection2DService,
        change_detection_2d_service: ChangeDetection2DService,
        segmentation_2d_service: Segmentation2DService,
        segmentation_3d_service: Segmentation3DService,
        project_service: ProjectService,
        id: int | None = None,
        type: str | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper | Response:
        if project_id:
            deleted_count = project_service.delete(project_id)
        else:
            if not id:
                return Response(
                    ResponseWrapper(code=3, message="Id is required"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            match type:
                case "segmentation":
                    deleted_count = segmentation_2d_service.delete(id=id)
                case "detection":
                    deleted_count = detection_2d_service.delete(id=id)
                case "change_detection":
                    deleted_count = change_detection_2d_service.delete(id=id)
                case "segmentation_3d":
                    deleted_count = segmentation_3d_service.delete(id=id)
                case _:
                    raise ValidationException

        if deleted_count:
            return ResponseWrapper(message="Analysis task deleted successfully")
        else:
            return Response(
                ResponseWrapper(code=2, message="Failed to delete project"),
                status_code=HTTP_400_BAD_REQUEST,
            )
