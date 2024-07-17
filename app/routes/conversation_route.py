from typing import Any, ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post, put
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import get_services
from app.utils.connections_manager import ConnectionsManager


class ConversationController(Controller):
    path = "/conversation"

    @get(path="/", sync_to_thread=True)
    def get(self, id: int | None = None) -> ResponseWrapper:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            conversation_service = services.conversation_service

            logger.debug("Getting Conversation")

            result = (
                conversation_service.get(id=id) if id else conversation_service.gets()
            )

            # logger.debug(f"Result: {result}")
            logger.debug("Got Conversation")

            return ResponseWrapper(result)

    @post(path="/", sync_to_thread=True)
    def create(self, data: dict) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            conversation_service = services.conversation_service

            logger.debug(f"Creating Conversation: {data}")
            if not data:
                return Response(
                    ResponseWrapper(code=3, message="Data is required"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            if "name" not in data:
                data["name"] = "未命名对话"

            conversation = conversation_service.create(**data)

            if not conversation:
                return Response(
                    ResponseWrapper(code=2, message="Failed to create conversation"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            return ResponseWrapper(
                conversation, message="Analysis task created successfully"
            )

    @put(path="/{id:int}", sync_to_thread=True)
    def update(self, data: list, id: int) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            conversation_service = services.conversation_service

            logger.debug(f"Updating Conversation: {data}")

            if not data:
                return Response(
                    ResponseWrapper(code=3, message="Data is required"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            conversation = conversation_service.update(id, data)

            if not conversation:
                return Response(
                    ResponseWrapper(code=2, message="Failed to update conversation"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            return ResponseWrapper(
                conversation, message="Analysis task updated successfully"
            )

    @delete(path="/", status_code=HTTP_200_OK, sync_to_thread=True)
    def remove(
        self, id: int | None = None, project_id: int | None = None
    ) -> ResponseWrapper | Response:
        with ConnectionsManager() as connections_manager:
            services = get_services(
                connections_manager.queries,
                connections_manager.minio_client,
                connections_manager.redis_client,
            )
            conversation_service = services.conversation_service

            logger.debug(f"Deleting Conversation: {id}")

            deleted_count = 0
            if id or project_id:
                deleted_count = conversation_service.delete(
                    id=id, project_id=project_id
                )
            else:
                return Response(
                    ResponseWrapper(code=3, message="Id is required"),
                    status_code=HTTP_400_BAD_REQUEST,
                )

            if deleted_count:
                return ResponseWrapper(message="Analysis task deleted successfully")
            else:
                return Response(
                    ResponseWrapper(code=2, message="Failed to delete project"),
                    status_code=HTTP_400_BAD_REQUEST,
                )
