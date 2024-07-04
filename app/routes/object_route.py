import mimetypes
from pathlib import Path
import tempfile
from typing import Annotated, ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post, put
from litestar.datastructures import State, UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import ObjectService


def object_service_provider(state: State) -> ObjectService:
    return ObjectService(state.queries, state.minio_client)


class ObjectController(Controller):
    path = "/object"
    dependencies: ClassVar = {
        "object_service": Provide(object_service_provider, sync_to_thread=False)
    }

    @get(path="/", sync_to_thread=True)
    def gets(self, object_service: ObjectService, type: str) -> ResponseWrapper: ...

    @get(path="/{id:int}", sync_to_thread=True)
    def get(
        self, id: int, object_service: ObjectService, type: str | None = None
    ) -> ResponseWrapper:
        match type:
            case "image":
                object_info = object_service.get_image(id)
            case "pointcloud":
                object_info = object_service.get_pointcloud(id)
            case None:
                object_info = object_service.get(id)

        if not object_info:
            return Response(
                ResponseWrapper(code=2, message=f"object_info with id {id} not found"),
                status_code=HTTP_404_NOT_FOUND,
            )
        return ResponseWrapper(object_info)

    @post(path="/", sync_to_thread=True)
    def create(
        self,
        data: Annotated[
            list[UploadFile], Body(media_type=RequestEncodingType.MULTI_PART)
        ],
        object_service: ObjectService,
    ) -> ResponseWrapper | Response:
        logger.info("Creating object")

        for file in data:
            mime_type, _ = mimetypes.guess_type(file.filename, strict=False)
            if not mime_type:
                return Response(
                    ResponseWrapper(code=3, message="Invalid file type"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            mime_type = Path(mime_type)

            # 创建NamedTemporaryFile对象，用于保存上传的文件
            suffix = Path(file.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                tmp_file = Path(f.name)
                f.write(file.file.read())

            if mime_type.parent.name == "image":
                id = object_service.save_image(
                    file.filename, tmp_file, content_type=str(mime_type)
                )
            elif mime_type.name in ["octet-stream", "vnd.las", "vnd.laz"]:
                id = object_service.save_pointcloud(
                    file.filename, tmp_file, content_type=str(mime_type)
                )
            else:
                return Response(
                    ResponseWrapper(code=3, message="Invalid file type"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            tmp_file.unlink()

        if not id:
            return Response(
                ResponseWrapper(code=1, message="Failed to create object"),
                status_code=HTTP_404_NOT_FOUND,
            )

        return Response(
            ResponseWrapper(message="Object created successfully", id=id),
            status_code=HTTP_201_CREATED,
        )

    @put(path="/{id:int}", sync_to_thread=True)
    def update(
        self,
        id: int,
        data: UploadFile,
        object_service: ObjectService,
        type: str | None = None,
    ) -> ResponseWrapper | Response:
        if not object_service.get(id):
            return Response(
                ResponseWrapper(code=2, message=f"Project with id {id} not found"),
                status_code=HTTP_404_NOT_FOUND,
            )

        match type:
            case "image":
                object_service.update_image(id, data.file)
            case "pointcloud":
                object_service.update_pointcloud(id, data.file)
            case None:
                mime_type, _ = mimetypes.guess_type(data.filename, strict=False)
                if not mime_type:
                    return Response(
                        ResponseWrapper(code=3, message="Invalid file type"),
                        status_code=HTTP_400_BAD_REQUEST,
                    )
                if mime_type.startswith("image"):
                    object_service.update_image(id, data.file)
                elif mime_type == "application/octet-stream":
                    object_service.update_pointcloud(id, data.file)
                else:
                    return Response(
                        ResponseWrapper(code=3, message="Invalid file type"),
                        status_code=HTTP_400_BAD_REQUEST,
                    )

        return ResponseWrapper(message="Object updated successfully")

    @delete(path="/{id:int}", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete(
        self, id: int, object_service: ObjectService
    ) -> ResponseWrapper | Response:
        if object_service.delete(id):
            return ResponseWrapper()
        return Response(
            ResponseWrapper(code=2, message=f"Project with id {id} not found"),
            status_code=HTTP_404_NOT_FOUND,
        )
