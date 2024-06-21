from typing import ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import Detection2DService


def detection_2d_service_provider(state: State) -> Detection2DService:
    return Detection2DService(state.queries)


class Detection2DController(Controller):
    path = "/2d-detection"
    dependencies: ClassVar = {
        "detection_2d_service": Provide(
            detection_2d_service_provider, sync_to_thread=False
        )
    }

    @get(path="/", sync_to_thread=True)
    def get(
        self,
        detection_2d_service: Detection2DService,
        id: int | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper:
        logger.debug("Getting 2d detection tasks")

        detections_2d = detection_2d_service.get(id=id, project_id=project_id)
        logger.debug(f"2d detections: {detections_2d}")

        return ResponseWrapper(detections_2d)

    @post(path="/", sync_to_thread=True)
    def create(
        self, data: dict, detection_2d_service: Detection2DService
    ) -> ResponseWrapper | Response:
        logger.debug(f"Creating 2d detection with data {data}")

        detection_id = detection_2d_service.create(**data)
        logger.debug(f"Detection id: {detection_id}")

        if detection_id:
            return ResponseWrapper(
                {"id": detection_id}, message="Project created successfully"
            )
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
        # if detection_2d_service.delete(project_id):
        #     return ResponseWrapper()
        if id:
            deleted_count = (detection_2d_service.delete(id=id),)
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
