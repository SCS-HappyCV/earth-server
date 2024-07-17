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
from app.services import get_services
from app.utils.connections_manager import ConnectionsManager


class ObjectController(Controller):
    path = "/object"

    @get(path="/", sync_to_thread=True)
    def get(
        self,
        id: int | None = None,
        ids: list[int] | None = None,
        object_id: int | None = None,
        type: str | None = None,
        origin_type: str | None = None,
        *,
        should_base64: bool = False,
        only_thumbnail: bool = False,
        start: int = 0,
        length: int = 9999,
    ) -> ResponseWrapper:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            object_service = services.object_service

            if ids and type == "image":
                logger.info("Getting images")
                object_info = object_service.get_images(
                    ids=ids, should_base64=should_base64, only_thumbnail=only_thumbnail
                )
            elif id or object_id:
                match type:
                    case "image":
                        logger.info("Getting image")
                        object_info = object_service.get_image(
                            id=id, object_id=object_id
                        )
                    case "pointcloud":
                        object_info = object_service.get_pointcloud(
                            id=id, object_id=object_id
                        )
                    case None:
                        object_info = object_service.get(id=object_id)
            else:
                origin_types = (origin_type,) if origin_type else None
                object_info = object_service.gets(
                    type=type, origin_types=origin_types, offset=start, row_count=length
                )
                total_count = object_service.count(type=type, origin_types=origin_types)

            if object_info is None:
                return Response(
                    ResponseWrapper(
                        code=2, message=f"object_info with id {id} not found"
                    ),
                    status_code=HTTP_404_NOT_FOUND,
                )

            if id or ids or object_id:
                return ResponseWrapper(object_info)

            return ResponseWrapper(
                {
                    "total": total_count,
                    "start": start,
                    "length": length,
                    "data": object_info,
                }
            )

    @post(path="/", sync_to_thread=True)
    def create(
        self,
        data: Annotated[
            list[UploadFile], Body(media_type=RequestEncodingType.MULTI_PART)
        ],
    ) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            object_service = services.object_service

            logger.info("Creating object")

            result = Box({"image_ids": [], "pointcloud_ids": [], "object_ids": []})
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
                    results = object_service.save_image(
                        file.filename, tmp_file, content_type=str(mime_type)
                    )
                    image_info = results.image_info

                    image_id, object_id = image_info.image_id, image_info.object_id
                    result.image_ids.append(image_id)
                    result.object_ids.append(object_id)
                elif mime_type.name in ["octet-stream", "vnd.las", "vnd.laz"]:
                    pointcloud_id, object_id = object_service.save_pointcloud(
                        file.filename, tmp_file, content_type=str(mime_type)
                    )
                    result.pointcloud_ids.append(pointcloud_id)
                    result.object_ids.append(object_id)
                else:
                    logger.debug(f"Invalid file type: {mime_type}")
                    return Response(
                        ResponseWrapper(code=3, message="Invalid file type"),
                        status_code=HTTP_400_BAD_REQUEST,
                    )

                tmp_file.unlink()

            if not result.object_ids:
                return Response(
                    ResponseWrapper(code=1, message="Failed to create object"),
                    status_code=HTTP_404_NOT_FOUND,
                )

            return Response(
                ResponseWrapper(result, message="Object created successfully"),
                status_code=HTTP_201_CREATED,
            )

    @put(path="/{id:int}", sync_to_thread=True)
    def update(
        self, id: int, data: UploadFile, type: str | None = None
    ) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            object_service = services.object_service

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

    @delete(path="/", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete(
        self,
        object_id: int | None = None,
        type: str | None = None,
        id: int | None = None,
    ) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            object_service = services.object_service

            logger.info("Deleting object")
            logger.info(f"object_id={object_id}, type={type}, id={id}")

            if object_service.delete(object_id):
                return ResponseWrapper()
            return Response(
                ResponseWrapper(
                    code=2, message=f"Object with id {object_id} not found"
                ),
                status_code=HTTP_404_NOT_FOUND,
            )
