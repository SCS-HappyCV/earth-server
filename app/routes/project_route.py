from typing import ClassVar

from box import Box
from litestar import Controller, Request, Response, delete, get, post, put
from litestar.datastructures import State
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from loguru import logger

from app.schemas import ResponseWrapper
from app.services import ProjectService


def project_service_provider(state: State) -> ProjectService:
    return ProjectService(state.queries)


class ProjectController(Controller):
    path = "/project"
    dependencies: ClassVar = {
        "project_service": Provide(project_service_provider, sync_to_thread=False)
    }

    @get(path="/", sync_to_thread=True)
    def gets(self, project_service: ProjectService) -> ResponseWrapper:
        logger.debug("Getting projects")

        projects = project_service.list()
        logger.debug(f"Projects: {projects}")

        return ResponseWrapper(projects)

    @get(path="/{id:int}", sync_to_thread=True)
    def get(self, id: int, project_service: ProjectService) -> ResponseWrapper:
        logger.debug(f"Getting project with id {id}")

        project_info = project_service.get(id)
        logger.debug(f"Project: {project_info}")

        project_info = Box(project_info)

        if not project_info:
            return Response(
                ResponseWrapper(code=2, message=f"Project with id {id} not found"),
                status_code=HTTP_404_NOT_FOUND,
            )
        return ResponseWrapper(project_info)

    @post(path="/", sync_to_thread=True)
    def create(
        self, data: dict, project_service: ProjectService
    ) -> ResponseWrapper | Response:
        logger.debug(f"Creating project with data {data}")

        project_id = project_service.create(**data)

        if project_id:
            return ResponseWrapper(
                {"id": project_id}, message="Project created successfully"
            )
        return Response(
            ResponseWrapper(code=1, message="Failed to create project"),
            status_code=HTTP_404_NOT_FOUND,
        )

    @delete(path="/{id:int}", status_code=HTTP_200_OK, sync_to_thread=True)
    def delete(
        self, id: int, project_service: ProjectService
    ) -> ResponseWrapper | Response:
        if project_service.delete(id):
            return ResponseWrapper()
        return Response(
            ResponseWrapper(code=2, message=f"Project with id {id} not found"),
            status_code=HTTP_404_NOT_FOUND,
        )

    @put(path="/{id:int}", sync_to_thread=True)
    def update(
        self, data: dict, id: int, project_service: ProjectService
    ) -> ResponseWrapper | Response:
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
