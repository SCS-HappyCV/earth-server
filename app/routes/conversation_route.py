from typing import Any, ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post, put
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import ValidationException
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import ConversationService, ProjectService


def conversation_service_provider(state: State) -> ConversationService:
    return ConversationService(state.queries, state.minio_client)


class ConversationController(Controller):
    path = "/conversation"
    dependencies: ClassVar = {
        "conversation_service": Provide(
            conversation_service_provider, sync_to_thread=False
        )
    }

    @get(path="/", sync_to_thread=True)
    def get(
        self, conversation_service: ConversationService, id: int | None = None
    ) -> ResponseWrapper:
        logger.debug("Getting Conversation")

        result = conversation_service.get(id=id) if id else conversation_service.gets()

        # logger.debug(f"Result: {result}")
        logger.debug("Got Conversation")

        return ResponseWrapper(result)

    @post(path="/", sync_to_thread=True)
    def create(
        self, data: dict, conversation_service: ConversationService
    ) -> ResponseWrapper | Response:
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
    def update(
        self, data: list, conversation_service: ConversationService, id: int
    ) -> ResponseWrapper | Response:
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
        self,
        project_service: ProjectService,
        id: int | None = None,
        project_id: int | None = None,
    ) -> ResponseWrapper | Response:
        if project_id:
            deleted_count = project_service.delete(project_id)
        elif not id:
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
