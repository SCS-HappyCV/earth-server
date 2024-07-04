from typing import ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import (
    ChangeDetection2DService,
    Detection2DService,
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
    }

    @get(path="/{type:str}", sync_to_thread=True)
    def get(
        self,
        type: str,
        segmentation_2d_service: Segmentation2DService,
        detection_2d_service: Detection2DService,
        change_detection_2d_service: ChangeDetection2DService,
        segmentation_3d_service: Segmentation3DService,
        id: int | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper:
        logger.debug("Getting 2d segmentation tasks")

        match type:
            case "segmentation":
                result = segmentation_2d_service.get(id=id, project_id=project_id)
            case "detection":
                result = detection_2d_service.get(id=id, project_id=project_id)
            case "change_detection":
                result = change_detection_2d_service.get(id=id, project_id=project_id)
            case "segmentation_3d":
                result = segmentation_3d_service.get(id=id, project_id=project_id)
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
            case "segmentation":
                segementaiton_3d_id = segmentation_2d_service.create(**data)
            case "detection":
                detection_2d_id = detection_2d_service.create(**data)
            case "change_detection":
                change_detection_2d_id = change_detection_2d_service.create(**data)
            case "segmentation_3d":
                segementaiton_3d_id = segmentation_3d_service.create(**data)
            case _:
                raise ValidationException

        if segementaiton_3d_id:
            return ResponseWrapper(
                {"id": segementaiton_3d_id}, message="Project created successfully"
            )
        elif detection_2d_id:
            return ResponseWrapper(
                {"id": detection_2d_id}, message="Project created successfully"
            )
        elif change_detection_2d_id:
            return ResponseWrapper(
                {"id": change_detection_2d_id}, message="Project created successfully"
            )
        else:
            return Response(
                ResponseWrapper(code=1, message="Failed to create project"),
                status_code=HTTP_404_NOT_FOUND,
            )

    @delete(path="/", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete(
        self,
        detection_2d_service: Detection2DService,
        id: int | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper | Response:
        if id:
            deleted_count = detection_2d_service.delete(id=id)
        elif project_id:
            deleted_count = detection_2d_service.delete(project_id=project_id)
        else:
            raise ValidationException

        if deleted_count:
            return ResponseWrapper(
                message=f"Deleted {deleted_count} 2d detections successfully"
            )
        else:
            return Response(
                ResponseWrapper(code=2, message="Failed to delete project"),
                status_code=HTTP_404_NOT_FOUND,
            )
